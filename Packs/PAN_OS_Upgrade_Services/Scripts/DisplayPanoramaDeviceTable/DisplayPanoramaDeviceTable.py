import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
This is an indicator-layout widget that displays the Devices connected to Panorama.
"""
MAX_PAGE_SIZE = 100
HEADERS = ["ID", "Hostname", "Software Version"]


def get_matching_relationships(target: str):
    """
    Searches for related CVE indicators to the given target.
    """
    indicators = demisto.internalHttpRequest('POST', '/relationships/search', {
        "page": 0,
        "size": 1000,
        "query": "",
        "sort": [
            {
                "field": "id",
                "asc": False
            }
        ],
        "entities": [
            target
        ],
        "entityTypes": [],
        "attachIndicators": True,
        "entityFamilies": [
            "Indicator"
        ]
    }).get('body')

    return json.loads(indicators).get("indicators")


def build_table(indicators: List[dict]):
    cve_table = []
    for indicator in indicators:
        if indicator.get("indicator_type") == "Network Device":
            device_name = indicator.get("value")
            device_id = indicator.get("id")
            cve_table.append({
                "ID": f"[{device_name}](/#/indicator/{device_id})",
                "Hostname": indicator.get("CustomFields").get("hostname"),
                "Software Version": indicator.get("CustomFields").get("softwareversion"),
            })

    return cve_table


def main():
    indicator = demisto.args().get("indicator")
    target = indicator.get("value")

    indicators = get_matching_relationships(target)

    if not indicators:
        markdown = """## No Devices Currently connected to this Panorama Server"""

        demisto.results({
            'Type': entryTypes['note'],
            'Contents': markdown,
            'ContentsFormat': formats['markdown'],
        })
        return

    cve_table = build_table(indicators)

    markdown = tableToMarkdown("", cve_table, headers=HEADERS)
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': markdown,
        'ContentsFormat': formats['markdown'],
    })


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
