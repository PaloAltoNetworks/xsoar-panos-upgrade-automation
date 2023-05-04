from typing import List, Optional
import demistomock as demisto
from CommonServerPython import *
from CommonServerUserPython import *

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


def parse_session(session_str: str):
    source, destination, port = session_str.split("/")
    return {
        "source": source,
        "destination": destination,
        "dest_port": port
    }


def run_snapshot(
        firewall: FirewallProxy, snapshot_list: Optional[List] = None):
    checks = CheckFirewall(firewall)
    """Runs a snapshot and saves it as a JSON file in the XSOAR system."""

    if not snapshot_list:
        snapshot_list = [
            'nics',
            'routes',
            'license',
            'arp_table',
            'content_version',
            'session_stats',
            'ip_sec_tunnels',
        ]

    snapshot = checks.run_snapshots(snapshot_list)

    return snapshot


def run_readiness_checks(
        firewall: FirewallProxy,
        check_list: Optional[List] = None,
        min_content_version: Optional[str] = None,
        candidate_version: Optional[str] = None,
        dp_mp_clock_diff: Optional[int] = None,
        ipsec_tunnel_status: Optional[str] = None,
        check_session_exists: Optional[str] = None,
):
    """
    Run all the readiness checks and return an xsoar-compatible result.

    :arg firewall: Firewall object
    :arg check_list: List of basic checks
    :arg min_content_version: The minimum content version to check for, enables "content_version" check
    :arg candidate_version: The candidate version to runchecks against. Enables "free_disk_space" check
    :arg dp_mp_clock_diff: The drift allowed between DP clock and MP clock. Enabled "planes_clock_sync" check.
    :arg ipsec_tunnel_status: Check a specific IPsec - by tunnel name. Tunnel must be up for this check to pass.
    :arg check_session_exists: Check for the presence of a specific connection.
        Session check format is <source>/destination/destination-port
        example: 10.10.10.10/8.8.8.8/443
    """

    if not check_list:
        # Setup the defaults
        check_list = [
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

    if dp_mp_clock_diff:
        custom_checks.append({
            "planes_clock_sync": {
                'diff_threshold': dp_mp_clock_diff
            }
        })

    if ipsec_tunnel_status:
        custom_checks.append({
            'ip_sec_tunnel_status': {
                'tunnel_name': ipsec_tunnel_status
            }
        })

    if check_session_exists:
        try:
            check_value = parse_session(check_session_exists)
        except ValueError:
            raise ValueError(
                f"{check_session_exists} is not a valid session string. Must be 'source/destination/port'."
            )
        custom_checks.append({
            "session_exist": check_value
        })

    check_config = check_list + custom_checks

    checks = CheckFirewall(firewall)
    results = checks.run_readiness_checks(check_config)

    return results


def convert_readiness_results_to_table(results: dict):
    table = []
    for key, result in results.items():
        table.append({
            "Test": key,
            **result
        })

    return tableToMarkdown("Readiness Check Results", table, headers=["Test", "state", "reason"])


def command_run_readiness_checks(panorama: Panorama):
    args = demisto.args()
    firewall = get_firewall_object(panorama, args.get("firewall_serial"))
    del args["firewall_serial"]
    results = run_readiness_checks(firewall, **args)

    return CommandResults(
        outputs={
            "ReadinessCheckResults": results,
            "Firewall": firewall.serial
        },
        readable_output=convert_readiness_results_to_table(results),
        outputs_prefix="FirewallAssurance"
    )


def command_run_snapshot(panorama: Panorama):
    args = demisto.args()
    firewall = get_firewall_object(panorama, args.get("firewall_serial"))
    snapshot_name = args.get("snapshot_name")
    del args["firewall_serial"]
    snapshot = run_snapshot(firewall, **args)
    fr = fileResult(
        snapshot_name, json.dumps(snapshot, indent=4)
    )
    return fr


def main():
    panorama_ip = demisto.params().get("url")
    panorama_user = demisto.params().get("panorama_user")
    panorama_password = demisto.params().get("panorama_password")
    panorama = get_panorama(panorama_ip, panorama_user, panorama_password)

    command = demisto.command()
    if command == "pan-os-assurance-run-readiness-checks":
        return_results(command_run_readiness_checks(panorama))
    if command == "pan-os-assurance-run-snapshot":
        return_results(command_run_snapshot(panorama))
    elif command == "test-module":
        return_results("ok")
    else:
        return_error(f"{command} not implemented.")


if __name__ == "__builtin__" or __name__ == "builtins":
    main()