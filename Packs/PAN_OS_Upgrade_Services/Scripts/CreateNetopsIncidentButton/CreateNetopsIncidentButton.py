import demistomock as demisto
from CommonServerPython import *  # noqa: F401

"""
This script is executed whenever a button in the Network Device or Panorama Device indicator layout is pressed.
"""


def main():
    indicator = demisto.args()["indicator"]
    target = str(indicator["value"])
    # Target for Panorama Device will be IP, not serial.
    if indicator.get("indicator_type") == "Panorama Device":
        target = str(indicator.get("CustomFields").get("panoramahostname"))
        if not target:
            target = str(indicator.get("CustomFields").get("ipaddress"))

    incident_type = demisto.args()["incident_type"]

    # Get pan-os instance name 
    panos = str(indicator.get("CustomFields").get('panoramainstance'))

    res = demisto.executeCommand("createNewIncident", {
        "name": f"{target} - {incident_type}",
        "type": incident_type,
        "panosnetworkoperationstarget": target,
        "panosnetworkoperationspanoramainstance": panos
    })

    created_incident = res[0]
    id = created_incident.get("EntryContext", dict()).get("CreatedIncidentID")

    demisto.executeCommand("associateIndicatorToIncident", {"incidentId": id, "value": indicator["value"]})


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
