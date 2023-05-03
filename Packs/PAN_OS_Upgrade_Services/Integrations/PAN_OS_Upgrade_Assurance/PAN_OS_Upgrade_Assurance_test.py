import os

import pytest


@pytest.fixture
def firewall_object():
    ip = os.getenv("PANORAMA_IP")
    user = os.getenv("PANORAMA_USERNAME")
    password = os.getenv("PANORAMA_PASSWORD")
    firewall_serial = os.getenv("FIREWALL_SERIAL")
    if not ip or not user or not password or not firewall_serial:
        pytest.skip("Missing required environment variables.")

    from PAN_OS_Upgrade_Assurance import get_panorama, get_firewall_object
    panorama = get_panorama(ip, user, password)
    return get_firewall_object(panorama, firewall_serial)


def test_setup(firewall_object):
    assert firewall_object


def test_run_readiness_checks(firewall_object):
    from PAN_OS_Upgrade_Assurance import run_readiness_checks
    bool_checks = [
        'panorama',
        'ntp_sync',
        'candidate_config',
        'expired_licenses',
        'ha'
    ]

    results = run_readiness_checks(
        firewall_object,
        bool_checks=bool_checks,
        min_content_version="8153-0000",
        candidate_version="10.1.6"
    )
    for k in bool_checks:
        assert k in results

    custom_checks = ["free_disk_space", "content_version"]
    for k in custom_checks:
        assert k in results

    print(results)
