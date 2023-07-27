import os

import pytest
test_password = os.getenv("TEST_PASSWORD")


def test_ssh():

    if not test_password:
        pytest.skip()
    from SetupFirewallFirstLogin import ssh_configure_admin
    ssh_configure_admin("192.168.1.166", test_password)
