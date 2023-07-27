import panos.errors

import demistomock as demisto
from CommonServerPython import *  # noqa: F401
from panos.device import SystemSettings
from panos.firewall import Firewall

DEFAULT_PAN_USERNAME = "admin"


def setup_system_settings(
        firewall: Firewall,
        panorama_ip_1: str,
        panorama_ip_2: Optional[str] = "",
        use_dhcp: Optional[bool] = True,
        firewall_hostname: Optional[str] = ""
):
    """Configure the firewall to point to panorama and, if requested, with DHCP for it's management interface."""
    system_settings = SystemSettings.refreshall(firewall)
    for system_setting in system_settings:
        system_setting.panorama = panorama_ip_1
        if panorama_ip_2:
            system_setting.panorama2 = panorama_ip_2

        if use_dhcp:
            system_setting.dhcp_send_hostname = True
            system_setting.dhcp_send_client_id = True

        if firewall_hostname:
            system_setting.hostname = firewall_hostname

        system_setting.apply()


def set_auth_key(firewall: Firewall, key: str):
    firewall.op(f"<request><authkey><set>{key}</set></authkey></request>", cmd_xml=False)


def setup_firewall(
        hostname,
        new_password: str,
        panorama_ip_1: str,
        panorama_ip_2: Optional[str] = "",
        device_auth_key: Optional[str] = "",
        use_dhcp: Optional[bool] = True,
        firewall_hostname: Optional[str] = "",
        default_username=DEFAULT_PAN_USERNAME,
):
    """Sets up the firewall, assuming it has been powered on and is available at `hostname` with the given credentials."""
    result = {}
    firewall = Firewall(
        hostname=hostname,
        api_password=new_password,
        api_username=default_username
    )
    # Point the firewall at Panorama and configure the management interface
    setup_system_settings(firewall, panorama_ip_1, panorama_ip_2, use_dhcp=use_dhcp, firewall_hostname=firewall_hostname)
    if device_auth_key:
        try:
            set_auth_key(firewall, device_auth_key)
            result["set_authkey"] = "Yes"
        except panos.errors.PanXapiError:
            result["set_authkey"] = f"Failed to set Authkey - May not be supported in {firewall.version}"

    firewall.commit()

    return {
        "ip": hostname,
        "new_hostname": firewall_hostname,
        "using_dhcp": use_dhcp,
        "serial": firewall.serial,
        **result
    }


def main():
    args = demisto.args()

    outputs = setup_firewall(
        args.get("hostname"),
        new_password=args.get("password"),
        panorama_ip_1=args.get("panorama_ip"),
        panorama_ip_2=args.get("backup_panorama_ip"),
        use_dhcp=argToBoolean(args.get("use_dhcp_for_management")),
        firewall_hostname=args.get("new_hostname"),
        device_auth_key=args.get("device_auth_key")
    )
    return_results(
        CommandResults(
            outputs_prefix="SetupFirewallForOnboarding",
            outputs=outputs,
            readable_output=tableToMarkdown("Onboarded firewall", outputs)
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
