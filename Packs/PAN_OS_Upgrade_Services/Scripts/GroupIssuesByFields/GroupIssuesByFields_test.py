import json


def test_group():
    issues = json.load(open("test_data/issues.json"))
    expected = json.load(open("test_data/expected_groups.json"))
    from GroupIssuesByFields import group_by_location_and_rulebase
    result = group_by_location_and_rulebase(issues)
    assert result == expected