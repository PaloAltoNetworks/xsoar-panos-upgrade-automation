import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401



"""
This script is executed whenever an associated button in the Network Device indicator layout is pressed.
"""


def main():
    args = demisto.args()
    indicator = args.get("indicator")
    target = str(indicator["value"])
    # Target for Panorama Device will be IP, not serial.
    if indicator.get("indicator_type") == "Panorama Device":
        target = str(indicator.get("CustomFields").get("panoramahostname"))
        if not target:
            target = str(indicator.get("CustomFields").get("ipaddress"))

    incident_type = args.get("incident_type")
    readiness_checklist = args.get("readiness_checklist")
    min_content_version = args.get("min_content_version")
    arp_entry_exists = args.get("arp_entry_exists")
    session_exists = args.get("session_exists")
    ipsec_tunnel = args.get("ipsec_tunnel")
    dp_mp_clock_diff = args.get("dp_mp_clock_diff")

    # Get pan-os instance name
    panos = str(indicator.get("CustomFields").get('panoramainstance'))

    res = demisto.executeCommand("createNewIncident", {
        "name": f"{target} - {incident_type}",
        "type": incident_type,
        "panosnetworkoperationstarget": target,
        "panosnetworkoperationspanoramainstance": panos,
        "readinesschecklist": readiness_checklist,
        "minimumcontentversion": min_content_version,
        "checkarpentryexists": arp_entry_exists,
        "checksessionexists": session_exists,
        "ipsectunnel": ipsec_tunnel,
        "dpmpclockdiff": dp_mp_clock_diff
    })

    created_incident = res[0]
    id = created_incident.get("EntryContext", dict()).get("CreatedIncidentID")

    demisto.executeCommand("associateIndicatorToIncident", {"incidentId": id, "value": indicator["value"]})


''' ENTRY POINT '''


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
