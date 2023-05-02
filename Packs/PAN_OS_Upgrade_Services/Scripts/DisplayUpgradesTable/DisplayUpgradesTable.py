import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
This is an indicator-layout widget script that displays the open or closed PAN-OS Upgrade incidents for this device .
"""
MAX_DAYS = 30
HEADERS = ["Incident", "name", "description", "occurred"]


def get_matching_incidents(target: str):
    """
    Searches for incidents in the last MAX_DAYS interval and renders it as a table.
    """
    incidents = demisto.internalHttpRequest('POST', '/incidents/search', {
        "filter": {
            "query": f"-category:job type:'PAN-OS Network Operations - Device Upgrade' panosnetworkoperationstarget:{target}",
            "period": {
                "by": "day",
                "fromValue": MAX_DAYS
            }
        }
    }).get('body')

    return json.loads(incidents).get("data")


def add_fields(incidents: List[dict]):
    """Add additional data into incident table"""
    for incident in incidents:
        incident_id = incident.get("id")
        incident["Incident"] = f"[{incident_id}](/#/incident/{incident_id})"
        incident["description"] = incident.get("CustomFields").get("description")

    return incidents


def main():
    indicator = demisto.args().get("indicator")
    target = indicator.get("value")
    # If this is type Panorama, we have to use the IPaddress as the target.
    if indicator.get("indicator_type") == "Panorama Device":
        target = str(indicator.get("CustomFields").get("panoramahostname"))
        if not target:
            target = str(indicator.get("CustomFields").get("ipaddress"))

    incidents = get_matching_incidents(target)
    incidents = add_fields(incidents)
    if not incidents:
        markdown = """## No Open Upgrade incidents! [Historical issues can be tracked via the incidents page](/#/incidents)\n"""

        demisto.results({
            'Type': entryTypes['note'],
            'Contents': markdown,
            'ContentsFormat': formats['markdown'],
        })
        return

    markdown = tableToMarkdown(f"Upgrade Incidents - {MAX_DAYS} days", incidents, headers=HEADERS)
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': markdown,
        'ContentsFormat': formats['markdown'],
    })


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
