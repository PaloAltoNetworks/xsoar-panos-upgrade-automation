import json
import os

import pytest
from panos.panorama import Panorama
from lxml import etree

TEST_LOCATION_FROM_ROOT = "Packs/PAN_OS_Upgrade_Services/Integrations/PAN_OS_Device_Management/"


def load_xml_root_from_test_file(xml_file: str):
    """Given an XML file, loads it and returns the root element XML object."""
    try:
        data = etree.parse(xml_file).getroot()
    except OSError:
        data = etree.parse(TEST_LOCATION_FROM_ROOT + xml_file).getroot()

    return data


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

@pytest.fixture
def integration_test_fixture():
    """Test fixture for running integration tests"""
    return Panorama(
        hostname=os.getenv("HOSTNAME"),
        api_key=os.getenv("API_KEY")
    )


def test_check_fetch_issues(integration_test_fixture):
    """
    Integration test; Validates that the indicator fetching works correctly against a real device.
    """
    if not os.getenv("HOSTNAME"):
        pytest.skip("Integration test not enabled.")

    from PAN_OS_Device_Management import fetch_configuration_hygiene_indicators
    result = fetch_configuration_hygiene_indicators(integration_test_fixture)
    print(result)


def test_fetch_indicators(integration_test_fixture):
    """
    Integration test; Validates that the indicator fetching works correctly against a real device.
    """
    if not os.getenv("HOSTNAME"):
        pytest.skip("Integration test not enabled.")

    from PAN_OS_Device_Management import fetch_devices_as_indicators
    result_indicators = fetch_devices_as_indicators(integration_test_fixture)
    assert len(result_indicators) > 0
    assert result_indicators[-1].get("relationships")
    print(result_indicators)


def test_test_module(integration_test_fixture):
    """
    Integration test; validates that the test passes when connected to Panorama
    """
    if not os.getenv("HOSTNAME"):
        pytest.skip("Integration test not enabled.")

    from PAN_OS_Device_Management import test_module
    assert test_module(integration_test_fixture) == "ok"


def test_check_security_zones(integration_test_fixture):
    """
    Integration test; Validates that the indicator fetching works correctly against a real device.
    """
    if not os.getenv("HOSTNAME"):
        pytest.skip("Integration test not enabled.")

    from PAN_OS_Device_Management import check_security_zones
    result = check_security_zones(integration_test_fixture)
    print(result)


def test_check_security_rules(integration_test_fixture):
    """
    Integration test; Validates that the indicator fetching works correctly against a real device.
    """
    if not os.getenv("HOSTNAME"):
        pytest.skip("Integration test not enabled.")

    from PAN_OS_Device_Management import check_security_rules
    result = check_security_rules(integration_test_fixture)
    print(result)


def test_get_devicegroups(integration_test_fixture):
    """
    Integration test; Checks we can retrieve the device groups from Panorama correctly
    """
    if not os.getenv("HOSTNAME"):
        pytest.skip("Integration test not enabled.")

    from PAN_OS_Device_Management import get_devicegroups
    result_dgs = get_devicegroups(integration_test_fixture)
    assert len(result_dgs) > 0


@pytest.mark.parametrize("xml_file,expected_data_file", [
    ("test_data/show_system_info.xml", "test_data/show_system_info_expected.json")
])
def test_flatten_xml_to_dict(xml_file, expected_data_file):
    from PAN_OS_Device_Management import flatten_xml_to_dict

    expected_dict = load_json_from_test_file(expected_data_file)

    xml_element = load_xml_root_from_test_file(xml_file)
    result_dict = {}
    result_dict = flatten_xml_to_dict(xml_element, result_dict)
    assert result_dict == expected_dict


@pytest.mark.parametrize("data_file,expected_type", [
    ("test_data/show_system_info_expected.json", "Network Device"),
    ("test_data/show_system_info_expected_panorama.json", "Panorama Device"),
])
def test_system_to_indicator(data_file, expected_type):
    from PAN_OS_Device_Management import system_to_indicator
    expected_dict = load_json_from_test_file(data_file).get("result").get("system")
    result = system_to_indicator(expected_dict)
    assert result.get("type") == expected_type