import demistomock as demisto
from CommonServerPython import *  # noqa: F401
from itertools import groupby

"""
Given a table of BPA issues, groups them in a way that can be passed to the pan-os-bulk-update command
"""


def rulebase_key_func(item):
    return item.get("rulebase")


def location_key_func(item):
    return item.get("location")


def group_by_location_and_rulebase(table: List[dict]):
    result = []
    sorted_location_fields = sorted(table, key=location_key_func)
    for location, issues_grouped_by_location in groupby(sorted_location_fields, location_key_func):
        sorted_issues_grouped_by_location = sorted(issues_grouped_by_location, key=rulebase_key_func)
        for rulebase, issues_grouped_by_location_and_rulebase in groupby(list(sorted_issues_grouped_by_location), rulebase_key_func):
            result.append({
                "location": location,
                "rulebase": rulebase,
                "object_names": [i.get("name") for i in issues_grouped_by_location_and_rulebase]
            })

    return result


def main():
    issue_table = argToList(demisto.args().get("issue_table"))
    outputs = group_by_location_and_rulebase(issue_table)
    return_results(
        CommandResults(
            outputs_prefix="GroupIssuesByFields",
            outputs=outputs,
            readable_output=tableToMarkdown("Grouped Issues", outputs)
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
