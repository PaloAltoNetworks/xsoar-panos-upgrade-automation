import demistomock as demisto
from CommonServerPython import *  # noqa: F401

"""
Searches the TIM DB for device indicators based on the provided query string and returns them if found. 
"""


def search_indicators(query: str):
    result = []
    indicators = demisto.searchIndicators(
        query='(type:"Network Device" or type:"Panorama Device") ' + query,
        size=1000, page=0
    )
    for indicator in indicators.get("iocs"):
        hostid = indicator.get("value")
        if indicator.get("indicator_type") == "Panorama Device":
            hostid = str(indicator.get("CustomFields").get("panoramahostname"))
            if not hostid:
                hostid = str(indicator.get("CustomFields").get("ipaddress"))

        result.append({
            "hostid": hostid,
            "hostname": indicator.get("CustomFields").get("hostname"),
            "tags": indicator.get("CustomFields").get("devicetags"),
            "value": indicator.get("value")
        })

    return result


def main():
    query = demisto.args().get("query", "")
    outputs = search_indicators(query)
    return_results(
        CommandResults(
            outputs_prefix="GetDevicesByQuery",
            outputs=outputs,
            readable_output=tableToMarkdown("Device Query Result", outputs)
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
