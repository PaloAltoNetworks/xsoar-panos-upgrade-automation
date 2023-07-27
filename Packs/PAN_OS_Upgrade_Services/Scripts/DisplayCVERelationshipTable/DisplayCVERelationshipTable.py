import demistomock as demisto
from CommonServerPython import *  # noqa: F401

"""
This is an indicator-layout widget script that displays the open or closed PAN-OS Upgrade incidents for this device .
"""
MAX_PAGE_SIZE = 100
HEADERS = ["CVE", "Description", "Published", "Link"]
SECURITIES_URL = "https://security.paloaltonetworks.com/"


def get_matching_relationships(target: str):
    """
    Searches for related CVE indicators to the given target.
    """
    relationship_result = demisto.internalHttpRequest('POST', '/relationships/search', {
        "page": 0,
        "size": 500,
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

    result = json.loads(relationship_result)

    non_revoked_indicators = []
    indicators = result.get("indicators")
    relationships = result.get("data")
    for relationship in relationships:
        if not relationship.get("CustomFields"):
            continue

        if not relationship.get("CustomFields").get("revoked"):
            non_revoked_indicators.append(
                next(i for i in indicators if i.get("value") == relationship.get("entityB"))
            )

    return non_revoked_indicators


def build_table(indicators: List[dict]):
    cve_table = []
    for indicator in indicators:
        if indicator.get("indicator_type") == "CVE":
            cve_name = indicator.get("value")
            cve_table.append({
                "CVE": cve_name,
                "Description": indicator.get("CustomFields").get("cvedescription"),
                "Published": indicator.get("CustomFields").get("published"),
                "Link": f"[{cve_name} Details]({SECURITIES_URL}{cve_name})"
            })

    return cve_table


def main():
    indicator = demisto.args().get("indicator")
    target = indicator.get("value")

    indicators = get_matching_relationships(target)

    if not indicators:
        markdown = """## No CVEs matching this software version!"""

        demisto.results({
            'Type': entryTypes['note'],
            'Contents': markdown,
            'ContentsFormat': formats['markdown'],
        })
        return

    cve_table = build_table(indicators)

    markdown = tableToMarkdown(f"CVEs affecting this PAN-OS version", cve_table, headers=HEADERS)
    demisto.results({
        'Type': entryTypes['note'],
        'Contents': markdown,
        'ContentsFormat': formats['markdown'],
    })


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
