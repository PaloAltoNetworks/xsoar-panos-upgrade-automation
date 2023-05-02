import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
This script is executed whenever a button in the Network Device or Panorama Device indicator layout is pressed.

This script creates a configuration issue remediation incident and passes it the relevant query to match the indicators.
"""

INCIDENT_TYPE = "PAN-OS Network Operations - Configuration Issue Remediation"


def main():
    args = demisto.args()
    indicator = args.get("indicator")
    issue_value = str(indicator["value"])

    issue_id = indicator.get("CustomFields").get("issueid")
    object_name = indicator.get("CustomFields").get("issueobjectname")
    affected_rulebase = indicator.get("CustomFields").get("affected_rulebase")

    fix_type = args.get("fix_type")
    auto_fix = argToBoolean(args.get("auto_fix"))

    if fix_type == "device":
        target = str(indicator["value"])
        if indicator.get("indicator_type") == "Panorama Device":
            target = str(indicator.get("CustomFields").get("panoramahostname"))
            if not target:
                target = str(indicator.get("CustomFields").get("ipaddress"))

        query = f"issueaffecteddevice:{target}"
        incident_name = f"Remediate all issues affecting {target}"

    elif fix_type == "all":
        query = f"issueid:{issue_id}"
        if affected_rulebase:
            query = f"{query} affectedrulebase:{affected_rulebase}"
        incident_name = f"Remediate all {issue_id} issues"
    else:
        query = f"value:{issue_value}"
        incident_name = f"Remediate issue {issue_id} affecting {object_name}"

    res = demisto.executeCommand("createNewIncident", {
        "name": incident_name,
        "type": INCIDENT_TYPE,
        "issuequery": query,
        "autofix": auto_fix
    })

    created_incident = res[0]
    id = created_incident.get("EntryContext", dict()).get("CreatedIncidentID")

    demisto.executeCommand("associateIndicatorToIncident", {"incidentId": id, "value": issue_value})


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
