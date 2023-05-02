import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
This is an indicator-layout widget script that displays the OPEN PAN-OS Hygiene issues for this device .
"""
MAX_DAYS = 30


def get_matching_indicators(target: str):
    """
    Searches for open incidents in the last MAX_DAYS interval and renders it as a table.
    """
    incidents = demisto.internalHttpRequest('POST', '/indicators/search', {
        "page": 0,
        "size": 1000,
        "query": f"type:\"Network Configuration Issue\" expirationStatus:active issueaffecteddevice:{target}",
        "sort": [
            {
                "field": "calculatedTime",
                "asc": False
            }
        ],
        "period": {
            "by": "day",
            "fromValue": 7
        }
    }).get('body')

    return json.loads(incidents).get("iocObjects")


def build_table(indicators: List[dict]):
    """
    Converts the open issues in the issue tables to a single table
    """
    issues_table = []
    for indicator in indicators:
        bp_link = indicator.get("CustomFields").get("bestpracticelink")
        indicator_id = indicator.get("id")
        issues_table.append({
            "Link to Issue": f"[Link to Issue](/#/indicator/{indicator_id})",
            "Issue ID": indicator.get("CustomFields").get("issueid"),
            "Affected Object": indicator.get("CustomFields").get("issueobjectname"),
            "Issue Subtype": indicator.get("CustomFields").get("issuesubtype"),
            "Best Practice Link": f"[Palo Alto Best Practices]({bp_link})",
            "Fix": indicator.get("CustomFields").get("issueremediation"),
        })
    return issues_table


def main():
    indicator = demisto.args().get("indicator")
    target = indicator.get("value")
    # If this is type Panorama, we have to use the IPaddress as the target.
    if indicator.get("indicator_type") == "Panorama Device":
        target = str(indicator.get("CustomFields").get("panoramahostname"))
        if not target:
            target = str(indicator.get("CustomFields").get("ipaddress"))

    indicators = get_matching_indicators(target)
    if not indicators:
        markdown = """## No open Hygiene or Best Practice issues! Well done! [Historical issues can be tracked via the indicators page](/#/indicators)\n"""

        demisto.results({
            'Type': entryTypes['note'],
            'Contents': markdown,
            'ContentsFormat': formats['markdown'],
        })
        return

    issues_table = build_table(indicators)
    markdown = tableToMarkdown("Open Configuration Hygiene Issues in the last 30 days", issues_table)
    markdown = """*Configuration Hygiene issues cover a set of the same issues identified by the BPA.*
    *This table displays any issues that are currently "open" - that is, they are associated to a current Configuration Hygiene check incident.*\n""" + markdown
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': markdown,
        'ContentsFormat': formats['markdown'],
    })


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
