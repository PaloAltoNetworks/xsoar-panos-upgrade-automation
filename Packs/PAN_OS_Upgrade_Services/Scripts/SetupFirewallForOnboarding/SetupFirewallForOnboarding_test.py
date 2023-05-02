import os

import pytest
from panos.firewall import Firewall

test_password = os.getenv("TEST_PASSWORD")


@pytest.fixture
def test_firewall():
    if not test_password:
        return

    return Firewall(
        hostname="192.168.1.164",
        api_password=test_password,
        api_username="admin"
    )



def test_setup_panorama(test_firewall):
    if not test_password:
        pytest.skip()

    from SetupFirewallForOnboarding import setup_system_settings
    setup_system_settings(test_firewall, "192.168.1.145")
