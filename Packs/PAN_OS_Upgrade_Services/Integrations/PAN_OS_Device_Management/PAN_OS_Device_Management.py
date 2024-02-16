import demistomock as demisto
from CommonServerPython import *

import requests
from typing import List, Union, Optional

from dataclasses import dataclass
from panos.panorama import Panorama, DeviceGroup, Template
from panos.policies import Rulebase, PreRulebase, PostRulebase, SecurityRule, NatRule
from panos.firewall import Firewall
from panos.network import Zone
from panos.device import Vsys
from urllib.parse import urlparse

# Disable insecure warnings
requests.packages.urllib3.disable_warnings()

ISSUE_INDICATOR_TYPE = "Network Configuration Issue"


class PANOSCommands:
    SHOW_SYSTEM_INFO = "show system info"
    SHOW_DEVICES_ALL = "show devices all"
    SHOW_DEVICE_GROUPS = "show devicegroups"


class FieldMap:
    """Maps data from the PAN-OS responses into their associated indicator fields."""
    field_map = {
        "swversion": "softwareversion",
        "avversion": "antivirusversion",
        "model": "devicemodel",
        "operationalmode": "devicestatus",
        "lastcommitallstatesp": "lastcommitstate"
    }

    @staticmethod
    def replace(field_name):
        """Swap the name with it's mapped XSOAR name if it exists in the map"""
        return FieldMap.field_map.get(field_name, field_name)


def flatten_xml_to_dict(element, object_dict: dict):
    """
    Given an XML element, a dictionary, and a class, flattens the XML into the class.
    This is a recursive function that will resolve child elements.
    :param element: XML element object
    :param object_dict: A dictionary to populate with the XML tag text
    :param class_type: The class type that this XML will be converted to - filters the XML tags by it's attributes
    """
    for child_element in element:
        tag = child_element.tag

        # Replace hyphens in tags with underscores to match python attributes
        tag = tag.replace("-", "_")
        if child_element.text:
            object_dict[tag] = child_element.text

        if len(child_element) > 0:
            # Create a new dict and add it at this tag

            items = flatten_xml_to_dict(child_element, {})
            if items:
                if object_dict.get(tag):
                    if not isinstance(object_dict.get(tag), list):
                        object_dict[tag] = [object_dict[tag], items]
                    else:
                        object_dict[tag].append(items)
                else:
                    object_dict[tag] = items

    return object_dict


def handle_ha_field(ha_settings: dict):
    """Converts the HA settings into fields objects"""
    field_data = {}
    if not ha_settings:
        field_data["hastatus"] = "active"

        return field_data

    field_data["hastatus"] = ha_settings.get("state")
    field_data["hapeerdevice"] = ha_settings.get("peer")
    return field_data


def system_to_indicator(data: dict) -> dict:
    """
    Convert a dictionary representation of the PAN-OS system xml, turn it into an indicator.
    """
    indicator_type = "Network Device"
    family = data.get("family", "unknown").lower()
    model = data.get("model", "unknown").lower()
    system_mode = data.get("system_mode", "unknown").lower()
    if family == "pc" or model == "panorama" or system_mode == "panorama":
        indicator_type = "Panorama Device"

    field_data = {}
    # Sub out the underscores and map if required
    for field, value in data.items():
        field_name = FieldMap.replace(field.replace("_", ""))
        field_data[field_name] = value

    field_data = {**field_data, **handle_ha_field(data.get("ha"))}

    # Add model
    field_data["devicevendor"] = "Palo Alto Networks"
    return {
        "value": data.get("serial"),
        "type": indicator_type,
        "rawJSON": data,
        "fields": field_data
    }


def get_devicegroups(panorama: Panorama):
    """Gets the device-groups and the devices that belong to each"""
    device_dict = {}
    device_groups = panorama.op(PANOSCommands.SHOW_DEVICE_GROUPS).findall("./result/devicegroups/entry")
    for device_group in device_groups:
        device_group_name = device_group.attrib.get("name")
        devices = device_group.findall("./devices/entry")
        for device in devices:
            device_json = {
                "device_group_name": device_group_name
            }
            device_json = flatten_xml_to_dict(device, device_json)
            device_dict[device_json.get("serial")] = device_json

    return device_dict


def build_device_relationships(panorama_indicator: dict, device_indicators: List[dict]):
    """
    Relates individual firewall devices to Panorama.
    """
    entity_a = panorama_indicator.get("value")
    entity_a_type = panorama_indicator.get("type")
    relationship_list = []
    relationship_name = "related-to"
    for device_indicator in device_indicators:
        entity_b = device_indicator.get("value")
        entity_b_type = device_indicator.get("type")
        relationship_list.append(
            EntityRelationship(
                name=relationship_name,
                entity_a=entity_a,
                entity_a_type=entity_a_type,
                entity_b=entity_b,
                entity_b_type=entity_b_type
            ).to_indicator()
        )

    return relationship_list


def fetch_devices_as_indicators(panorama: Panorama, panos_instance: str) -> List[dict]:
    """
    Queries the Panorama system for managed devices and ingests them as indicators based on their type. Also queries Panorama
    itself for it's details and ingests it as an indicator as well.
    """
    indicators = []
    panorama_data = flatten_xml_to_dict(panorama.op(PANOSCommands.SHOW_SYSTEM_INFO).find("./result/system"), {})
    panorama_data = system_to_indicator(panorama_data)
    # Panorama device used by this integration is always considered connected
    panorama_data["fields"]["connected"] = "yes"
    # Panorama device used by this integration is always considered HA status Active
    panorama_data["fields"]["hastatus"] = "active"
    # Also set the Panorama IP; this is used as the target for many use cases and may differ from what Panorama says is it's own
    # IP.
    panorama_data["fields"]["panoramahostname"] = panorama.hostname
    # Set the panos instance 
    panorama_data["fields"]["panoramainstance"] = panos_instance

    devices = panorama.op(PANOSCommands.SHOW_DEVICES_ALL).findall("./result/devices/entry")
    device_groups = get_devicegroups(panorama)

    for device in devices:
        device_data = flatten_xml_to_dict(device, {})
        device_group = device_groups.get(device_data.get("serial"))
        # If the device is a member of a DG, then merge the fields
        if device_group:
            device_data = {**device_data, **device_group}
            # Set the tag field to the name of the DG
            device_data["devicetags"] = [device_data.get("device_group_name")]

        device_data = system_to_indicator(device_data)
        # Set the panos instance 
        device_data["fields"]["panoramainstance"] = panos_instance
        indicators.append(
            device_data
        )

    relationships = build_device_relationships(panorama_data, indicators)
    panorama_data["relationships"] = relationships
    indicators.append(panorama_data)
    return indicators


def get_all_rules_in_container(container: Union[Panorama, Firewall, DeviceGroup, Template, Vsys],
                               object_class: Union[SecurityRule, NatRule]):
    """
    Given a container (DG/template) and the class representing a type of rule object in pan-os-python, gets all the
    associated objects and yields them as a tuple of the rulebase they belong to, and the object themselves.

    :param container: Device group or template
    :param object_class: The pan-os-python class of objects to retrieve
    """
    if object_class not in [SecurityRule, NatRule]:
        raise ValueError(f"Given class {object_class} cannot be retrieved by this function.")

    firewall_rulebase = Rulebase()
    pre_rulebase = PreRulebase()
    post_rulebase = PostRulebase()
    container.add(pre_rulebase)
    container.add(post_rulebase)
    container.add(firewall_rulebase)

    for object in object_class.refreshall(firewall_rulebase):
        yield "rulebase", object

    for object in object_class.refreshall(pre_rulebase):
        yield "pre-rulebase", object

    for object in object_class.refreshall(post_rulebase):
        yield "post-rulebase", object


def get_all_configuration_parents(device: Union[Panorama, Firewall], name_filter: Optional[str] = ""):
    """Gets all the configuration parents like DG, template, vsys"""
    containers = []
    device_groups = DeviceGroup.refreshall(device)
    for device_group in device_groups:
        containers.append(device_group)

    templates = Template.refreshall(device)
    for template in templates:
        containers.append(template)

    virtual_systems = Vsys.refreshall(device)
    for virtual_system in virtual_systems:
        containers.append(virtual_system)

    if isinstance(device, Panorama):
        # Add the "shared" device if Panorama. Firewalls will always have vsys1
        containers.append(device)

    return_containers = []

    if name_filter:
        for container in containers:
            if name_filter == "shared":
                if isinstance(container, Panorama):
                    return_containers.append(container)
            if not isinstance(container, (Panorama, Firewall)):
                if container.name == name_filter:
                    return_containers.append(container)
    else:
        return_containers = containers

    return return_containers


class IssueSubtypes:
    VISIBILITY = "visibility"
    THREAT = "threat"


@dataclass
class ConfigurationHygieneIssue:
    """
    :param container_name: What parent container (DG, Template, VSYS) this object belongs to.
    :param issue_code: The shorthand code for the issue
    :param description: Human readable description of issue
    :param name: The affected object name
    """
    hostid: str
    object_name: str
    status: str

    device_group: str = ""
    template: str = ""
    vsys: str = ""
    rulebase: str = ""

    issue_id: str = ""
    description: str = ""

    remediation: str = ""
    best_practices_link: str = ""
    issue_subtype: str = ""
    affected_object_type: str = ""
    panos_instance: str = ""

    def as_indicator(self):
        return {
            "value": f"{self.hostid}_{self.issue_id}_{self.object_name}",
            "type": ISSUE_INDICATOR_TYPE,
            "fields": {
                "issueaffecteddevice": self.hostid,
                "issuedevicegroup": self.device_group,
                "issuetemplate": self.template,
                "issueobjectname": self.object_name,
                "issuesubtype": self.issue_subtype,
                "issuedescription": self.description,
                "issueremediation": self.remediation,
                "issuestatus": self.status,
                "bestpracticelink": self.best_practices_link,
                "affectedobjecttype": self.affected_object_type,
                "issueid": self.issue_id,
                "affectedrulebase": self.rulebase,
                "panoramainstance": self.panos_instance
            }
        }


@dataclass
class SecurityRuleNoLogAtSessionEnd(ConfigurationHygieneIssue):
    issue_id: str = "BP-V-8"
    description: str = """Enabling traffic logging is important for proper visibility of traffic in the environment. 
    
    Log at session end is recommended instead of at session start as the application used in the session may change over time.
    """

    remediation: str = """Enable Log at session end on the security rule."""
    best_practices_link: str = "https://knowledgebase.paloaltonetworks.com/KCSArticleDetail?id=kA10g000000Clt5CAC"
    issue_subtype: str = IssueSubtypes.VISIBILITY


@dataclass
class SecurityRuleNoLogForwardingProfile(ConfigurationHygieneIssue):
    issue_id: str = "BP-V-9"
    description: str = """In an environment where you use multiple firewalls to control and analyze network traffic, 
any single firewall can display logs and reports only for the traffic it monitors. 
Because logging in to multiple firewalls can make monitoring a cumbersome task, you can more efficiently achieve global visibility 
into network activity by forwarding the logs from all firewalls to Panorama or external services.

A log forwarding profile is also mandatory to forward logs to Panorama. 
    """

    remediation: str = """Enable a log forwarding profile on the security rule."""
    best_practices_link: str = "https://docs.paloaltonetworks.com/pan-os/10-2/pan-os-admin/monitoring/configure-log-forwarding"
    issue_subtype: str = IssueSubtypes.VISIBILITY


@dataclass
class SecurityRuleNoProfiles(ConfigurationHygieneIssue):
    issue_id: str = "BP-V-10"
    description: str = """Security profiles enable you to inspect network traffic for threats such as vulnerability exploits, malware, command-and-control (C2) communication, and even unknown threats, and prevent them from compromising your network using various types of threat signatures.
    """

    remediation: str = """Configure a security-profile-group with valid threat protection enabled on the security rule."""
    best_practices_link: str = "https://docs.paloaltonetworks.com/best-practices/9-1/internet-gateway-best-practices/best-practice-internet-gateway-security-policy/transition-safely-to-best-practice-security-profiles"
    issue_subtype: str = IssueSubtypes.THREAT


@dataclass
class SecurityZoneNoLogSetting(ConfigurationHygieneIssue):
    issue_id: str = "BP-V-7"
    description: str = """Zone-Protection protects Security Zones against flood and packet based attacks.
    
Without log forwarding, while zone protection will still be active, the threats and traffic being dropped by the profile will not
be visible."""

    remediation: str = """Add a log forwarding profile to the security zone"""
    best_practices_link: str = "https://docs.paloaltonetworks.com/best-practices/10-1/dos-and-zone-protection-best-practices/dos-and-zone-protection-best-practices/follow-post-deployment-dos-and-zone-protection-best-practices"
    issue_subtype: str = IssueSubtypes.VISIBILITY


def resolve_host_id(device):
    """
    Gets the ID of the host from a PanDevice object. This may be an IP address or serial number.
    :param device: `Pandevice` object instance, can also be a `Firewall` or `Panorama` type.
    """
    host_id: str = ""
    if device.hostname:
        host_id = device.hostname
    if device.serial:
        host_id = device.serial

    return host_id


def resolve_parent_to_kwarg(parent):
    if type(parent) is Panorama:
        return {"device_group": "shared"}

    map_dict = {
        DeviceGroup: {"device_group": parent.name},
        Template: {"template": parent.name},
        Vsys: {"vsys": parent.name}
    }
    return map_dict.get(type(parent))


def check_security_zones(device: Union[Panorama, Firewall], panos_instance: str, name_filter: Optional[str] = ""):
    """
    Check Palo Alto Security Zones for best practice issues
    """
    issue_objects = []
    for parent in get_all_configuration_parents(device, name_filter):
        security_zones: List[Zone] = Zone.refreshall(parent)
        for security_zone in security_zones:
            if not security_zone.log_setting:
                issue_objects.append(
                    SecurityZoneNoLogSetting(
                        hostid=resolve_host_id(device),
                        object_name=security_zone.name,
                        status="unresolved",
                        affected_object_type="SecurityZone",
                        panos_instance=panos_instance,
                        **resolve_parent_to_kwarg(parent)
                    )
                )

    return [x.as_indicator() for x in issue_objects]


def check_security_rules(device: Union[Panorama, Firewall], panos_instance: str, name_filter: Optional[str] = ""):
    """
    Check Palo Alto Security rules for best practice issues.
    """
    issue_objects = []
    for parent in get_all_configuration_parents(device, name_filter):
        for rulebase, security_rule in get_all_rules_in_container(parent, SecurityRule):
            if not security_rule.log_end:
                issue_objects.append(
                    SecurityRuleNoLogAtSessionEnd(
                        hostid=resolve_host_id(device),
                        object_name=security_rule.name,
                        status="unresolved",
                        affected_object_type="SecurityRule",
                        rulebase=rulebase,
                        panos_instance=panos_instance,
                        **resolve_parent_to_kwarg(parent)
                    )
                )

            if not security_rule.log_setting:
                issue_objects.append(
                    SecurityRuleNoLogForwardingProfile(
                        hostid=resolve_host_id(device),
                        object_name=security_rule.name,
                        status="unresolved",
                        affected_object_type="SecurityRule",
                        rulebase=rulebase,
                        panos_instance=panos_instance,
                        **resolve_parent_to_kwarg(parent)
                    )
                )

            if not any([
                security_rule.group,
                all(
                    [
                        security_rule.virus,
                        security_rule.spyware,
                        security_rule.vulnerability,
                        security_rule.url_filtering,
                    ]
                )]
            ):
                issue_objects.append(
                    SecurityRuleNoProfiles(
                        hostid=resolve_host_id(device),
                        object_name=security_rule.name,
                        status="unresolved",
                        affected_object_type="SecurityRule",
                        rulebase=rulebase,
                        panos_instance=panos_instance,
                        **resolve_parent_to_kwarg(parent)
                    )
                )

    return [x.as_indicator() for x in issue_objects]


def fetch_configuration_hygiene_indicators(device: Union[Panorama, Firewall], panos_instance: str):
    """
    Runs through the series of configuration hygiene checks looking for best practice issues, and returns any that match.
    """
    indicators = []
    indicators += check_security_rules(device, panos_instance)
    indicators += check_security_zones(device, panos_instance)

    return indicators


def test_module(panorama: Panorama) -> str:
    """Tests this integration is configured by connecting to panorama and running an op command. Also validates this is indeed
    connecting to Panorama, as this is required for this integration to work."""
    result = panorama.op(PANOSCommands.SHOW_SYSTEM_INFO)
    result_dict = flatten_xml_to_dict(result.find("./result/system"), {})
    family = result_dict.get("family", "unknown").lower()
    model = result_dict.get("model", "unknown").lower()
    if family == "pc" or model == "panorama":
        return "ok"

    if family == "m" or model in ["m-500", "m-600"]:
        return "ok"

    raise ValueError(f"Incorrect model type; got family {family} and model {model} but must be panorama.")


def main():
    """Main entrypoint for script"""
    params = demisto.params()
    api_key = str(params.get('key')) or str((params.get('credentials') or {}).get('password', ''))
    parsed_url = urlparse(params.get("url"))
    port = params.get("port", "443")
    hostname = parsed_url.hostname
    panos_instance = str(params.get('panosIntegrationName', ''))

    handle_proxy()
    panorama = Panorama.create_from_device(
        hostname=hostname,
        api_key=api_key,
        port=port
    )
    command_name = demisto.command()
    if command_name == "test-module":
        return_results(test_module(panorama))
    elif command_name == "fetch-indicators":
        for b in batch(fetch_devices_as_indicators(panorama, panos_instance)):
            demisto.createIndicators(b)

        if argToBoolean(params.get("fetch_panorama_hygiene_issues", False)):
            for b in batch(fetch_configuration_hygiene_indicators(panorama, panos_instance)):
                demisto.createIndicators(b)


if __name__ == "__builtin__" or __name__ == "builtins":
    main()
