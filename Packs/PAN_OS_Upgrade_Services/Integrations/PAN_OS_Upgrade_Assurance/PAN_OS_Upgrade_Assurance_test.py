import json
import os
import demistomock as demisto
import pytest
from dotenv import load_dotenv

"""
Upgrade Assurance Python Tests
This test suite only tests the XSOAR integration components and functions.

To run integration tests, you need to specifiy the following environment variables;

    * PANORAMA_HOSTNAME
    * PANORAMA_API_KEY
    * PANORAMA_PORT
"""


@pytest.fixture
def panorama_object():
    load_dotenv()

    hostname = os.getenv("PANORAMA_HOSTNAME")
    api_key = os.getenv("PANORAMA_API_KEY")
    port = os.getenv("PANORAMA_PORT")
    if not hostname or not api_key or not port:
        pytest.skip("Missing required environment variables.")

    from panos.panorama import Panorama
    return Panorama.create_from_device(
        hostname=hostname,
        api_key=api_key,
        port=port
    )


@pytest.fixture
def firewall_object(panorama_object):
    firewall_serial = os.getenv("FIREWALL_SERIAL")
    if not firewall_serial:
        pytest.skip("Missing required environment variables.")

    from PAN_OS_Upgrade_Assurance import get_firewall_object
    return get_firewall_object(panorama_object, firewall_serial)


def test_setup(firewall_object):
    assert firewall_object


def test_parse_session_str():
    from PAN_OS_Upgrade_Assurance import parse_session
    d = parse_session("1.1.1.1/8.8.8.8/443")
    assert d == {"source": "1.1.1.1", "destination": "8.8.8.8", "dest_port": "443"}

    with pytest.raises(ValueError):
        parse_session("1.1.1.1/8.8.8.8")


def test_run_snapshot_report(firewall_object):
    from PAN_OS_Upgrade_Assurance import run_snapshot, compare_snapshots, convert_snapshot_result_to_table
    left_snapshot = run_snapshot(firewall_object)
    right_snapshot = run_snapshot(firewall_object)
    result = compare_snapshots(left_snapshot, right_snapshot)
    print(json.dumps(result, indent=4))
    print(convert_snapshot_result_to_table(result))


def test_run_readiness_checks(firewall_object):
    from PAN_OS_Upgrade_Assurance import run_readiness_checks, convert_readiness_results_to_table
    bool_checks = [
        'panorama',
        'ntp_sync',
        'candidate_config',
        'expired_licenses',
        'ha'
    ]

    results = run_readiness_checks(
        firewall_object,
        check_list=bool_checks,
        min_content_version="8153-0000",
        candidate_version="10.1.6",
        check_session_exists="10.10.10.10/8.8.8.8/443"
    )
    for k in bool_checks:
        assert k in results

    custom_checks = ["free_disk_space", "content_version", ]
    for k in custom_checks:
        assert k in results

    print(convert_readiness_results_to_table(results))


def test_run_command_readiness_checks(panorama_object):
    from PAN_OS_Upgrade_Assurance import command_run_readiness_checks

    def r_args():
        return {"firewall_serial": os.getenv("FIREWALL_SERIAL")}

    demisto.args = r_args
    print(command_run_readiness_checks(panorama_object).readable_output)
