from typing import List, Optional
from panos_upgrade_assurance.firewall_proxy import FirewallProxy
from panos_upgrade_assurance.check_firewall import CheckFirewall

from panos.panorama import Panorama


def get_firewall_object(panorama: Panorama, serial_number):
    """Create a FirewallProxy object and attach it to Panorama, so we can access it."""
    firewall = FirewallProxy(serial=serial_number)
    panorama.add(firewall)
    return firewall


def get_panorama(ip, user, password):
    """Create the Panorama Object"""
    return Panorama(
        api_username=user,
        api_password=password,
        hostname=ip
    )


def run_readiness_checks(
        firewall: FirewallProxy,
        bool_checks: Optional[List] = None,
        min_content_version: Optional[str] = None,
        candidate_version: Optional[str] = None,
):
    """
    Run all the readiness checks and return an xsoar-compatible result.

    :arg firewall: Firewall object
    :arg bool_checks: List of basic checks
    :arg min_content_version: The minimum content version to check for, enables "content_version" check
    :arg candidate_version: The candidate version to runchecks against. Enables "free_disk_space" check
    """

    if not bool_checks:
        # Setup the defaults
        bool_checks = [
            'panorama',
            'ntp_sync',
            'candidate_config',
            'expired_licenses',
        ]
    custom_checks = []
    # Add the custom checks
    if min_content_version:
        custom_checks.append({"content_version": {'version': min_content_version}})

    if candidate_version:
        custom_checks.append({
            "free_disk_space": {
                "image_version": candidate_version
            }
        })

    check_config = bool_checks + custom_checks

    checks = CheckFirewall(firewall)
    results = checks.run_readiness_checks(check_config)

    return results


def main():
    panorama_ip = demisto.params().get("panorama_ip")
    panorama_user = demisto.params().get("panorama_user")
    panorama_password = demisto.params().get("panorama_password")
