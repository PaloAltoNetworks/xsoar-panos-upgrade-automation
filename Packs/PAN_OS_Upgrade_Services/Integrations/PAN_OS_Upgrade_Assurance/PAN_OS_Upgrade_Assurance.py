from CommonServerPython import *

from typing import Optional, List

from panos_upgrade_assurance.firewall_proxy import FirewallProxy
from panos_upgrade_assurance.check_firewall import CheckFirewall
from panos_upgrade_assurance.snapshot_compare import SnapshotCompare

from panos.panorama import Panorama
from panos.errors import PanDeviceXapiError

SETTINGS = {
    "skip_force_locale": True
}


def get_file_path(input_entry_id):
    res = demisto.getFilePath(input_entry_id)
    if not res:
        return_error("Entry {} not found".format(input_entry_id))
    file_path = res['path']
    return file_path


def read_file_by_id(input_entry_id):
    fp = get_file_path(input_entry_id)
    return json.load(open(fp))


def get_firewall_object(panorama: Panorama, serial_number):
    """Create a FirewallProxy object and attach it to Panorama, so we can access it."""
    firewall = FirewallProxy(serial=serial_number)
    panorama.add(firewall._fw)
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
    checks = CheckFirewall(firewall, **SETTINGS)
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
        arp_entry_exists: Optional[str] = None
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
    :arg arp_entry_exists: Check for the prescence of a specific ARP entry.
        example: 10.0.0.6
    """

    if not check_list:
        # Setup the defaults
        check_list = [
            'panorama',
            'ntp_sync',
            'candidate_config',
            'expired_licenses',
            'ha'
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
    else:
        check_list.append('free_disk_space')

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

    if arp_entry_exists:
        custom_checks.append({
            'arp_entry_exist': {
                'ip': arp_entry_exists
            }
        })

    check_config = check_list + custom_checks

    checks = CheckFirewall(firewall, **SETTINGS)
    results = checks.run_readiness_checks(check_config)

    return results


def compare_snapshots(left_snapshot, right_snapshot):
    snapshot_compare = SnapshotCompare(left_snapshot, right_snapshot)

    defaults = [
        {'ip_sec_tunnels': {
            'properties': ['state']
        }},
        {'arp_table': {
            'properties': ['!ttl'],
            'count_change_threshold': 10
        }},
        {'nics': {
            'count_change_threshold': 10
        }},
        {'license': {
            'properties': ['!serial']
        }},
        {'routes': {
            'properties': ['!flags'],
            'count_change_threshold': 10
        }},
        'content_version',
        {'session_stats': {
            'thresholds': [
                {'num-max': 10},
                {'num-tcp': 10},
            ]
        }}
    ]
    return snapshot_compare.compare_snapshots(defaults)


def convert_readiness_results_to_table(results: dict):
    table = []
    for key, result in results.items():
        table.append({
            "Test": key,
            **result
        })

    return table


def convert_snapshot_result_to_table(results: dict):
    table = []
    for key, test_result in results.items():
        if type(test_result) is dict:
            table.append({
                "test": f"{key}",
                "passed": test_result.get("passed")
            })

    return table


def command_run_readiness_checks(panorama: Panorama):
    args = demisto.args()
    firewall = get_firewall_object(panorama, args.get("firewall_serial"))
    del args["firewall_serial"]
    results = run_readiness_checks(firewall, **args)

    return CommandResults(
        outputs={
            "ReadinessCheckResults": convert_readiness_results_to_table(results),
            "Firewall": firewall.serial
        },
        readable_output=tableToMarkdown("Readiness Check Results",
                                        convert_readiness_results_to_table(results),
                                        headers=["Test", "state", "reason"]),
        outputs_prefix="FirewallAssurance"
    )


def command_run_snapshot(panorama: Panorama):
    """Runs a single snapshot and returns it as a file."""
    args = demisto.args()
    firewall = get_firewall_object(panorama, args.get("firewall_serial"))
    snapshot_name = args.get("snapshot_name", "fw_snapshot")
    del args["firewall_serial"]
    if args.get("snapshot_name"):
        del args["snapshot_name"]
    snapshot = run_snapshot(firewall, **args)
    fr = fileResult(
        snapshot_name, json.dumps(snapshot, indent=4)
    )
    return fr


def command_compare_snapshots():
    """Compare two snapshot files, accepting th left and right snapshots as arguments."""
    args = demisto.args()
    left_snapshot = read_file_by_id(args.get("left_snapshot_id"))
    right_snapshot = read_file_by_id(args.get("right_snapshot_id"))
    result = compare_snapshots(left_snapshot, right_snapshot)
    return CommandResults(
        outputs={
            "SnapshotComparisonResult": convert_snapshot_result_to_table(result),
            "SnapshotComparisonRawResult": result
        },
        readable_output=tableToMarkdown(
            "Snapshot Comparison Results", convert_snapshot_result_to_table(result), headers=["test", "passed"]),
        outputs_prefix="FirewallAssurance"
    )


def main():
    panorama_ip = demisto.params().get("url")
    panorama_user = demisto.params().get("panorama_user")
    panorama_password = demisto.params().get("panorama_password")
    panorama = get_panorama(panorama_ip, panorama_user, panorama_password)

    handle_proxy()

    command = demisto.command()
    try:
        if command == "pan-os-assurance-run-readiness-checks":
            return_results(command_run_readiness_checks(panorama))
        elif command == "pan-os-assurance-run-snapshot":
            return_results(command_run_snapshot(panorama))
        elif command == "pan-os-assurance-compare-snapshots":
            return_results(command_compare_snapshots())
        elif command == "test-module":
            return_results("ok")
        else:
            return_error(f"{command} not implemented.")
    except PanDeviceXapiError as e:
        return_error(f"{e}")


if __name__ == "__builtin__" or __name__ == "builtins":
    main()
