import json

TEST_LOCATION_FROM_ROOT = "Packs/PAN_OS_Upgrade_Services/Scripts/GroupIssuesByFields/"


def load_json_from_test_file(file_name):
    """Given a JSON file, returns the contents"""
    try:
        with open(file_name) as f:
            data = json.load(f)
    except FileNotFoundError:
        # Handle test being run outside of test directory (i.e from content root dir)
        with open(TEST_LOCATION_FROM_ROOT + file_name) as f:
            data = json.load(f)
    
    return data


def test_group():
    issues = load_json_from_test_file("test_data/issues.json")
    expected = load_json_from_test_file("test_data/expected_groups.json")
    from GroupIssuesByFields import group_by_location_and_rulebase
    result = group_by_location_and_rulebase(issues)
    assert result == expected
