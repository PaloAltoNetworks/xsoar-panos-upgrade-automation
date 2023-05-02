import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
Runs a series of PAN-OS commands and pickles them into a Snapshot file.

Snapshots can then be compared to look for changes in operational state between the two.
"""


def run_command(command_name: str, command_args: {}):
    """Executes a single command and returns the result as a python object"""
    res = demisto.executeCommand(command_name, command_args)
    if is_error(res):
        return_error(get_error(res))

    data = res[0]['Contents']
    return data


def get_routing_details(target: Optional[str] = None):
    """
    Gets the routing table from the given target
    """
    command_args = {}
    if target:
        command_args["target"] = target
    result = run_command("pan-os-platform-get-routes", command_args)
    if result:
        return result.get("Result", [])
    else:
        return []


def get_bgp_peers(target: Optional[str] = None):
    """
    Gets the current BGP neighbor table from the target
    """
    command_args = {}
    if target:
        command_args["target"] = target
    result = run_command("pan-os-platform-get-bgp-peers", command_args)
    if result:
        return result.get("Result", [])
    else:
        return []



def get_arp_tables(target: Optional[str] = None):
    """
    Gets the current BGP neighbor table from the target
    """
    command_args = {}
    if target:
        command_args["target"] = target
    result = run_command("pan-os-platform-get-arp-tables", command_args)
    if result:
        return result.get("Result", [])
    else:
        return []



def take_snapshot(target: Optional[str] = None) -> str:
    """
    Takes a snapshot of all the operational state of the PAN-OS target device and returns it as a json string.
    """
    snapshot = {
        "routes": get_routing_details(target),
        "bgp_peers": get_bgp_peers(target),
        "arp": get_arp_tables(target),
    }

    snapshot_json = json.dumps(snapshot)
    return snapshot_json


def main():
    demisto_args = demisto.args()
    target = demisto_args.get("target")

    snapshot = take_snapshot(target)
    # Timestamp the file name
    time_string = int(datetime.now().timestamp())
    return_results(
        fileResult(
            f"{target}_System_Snapshot_{time_string}.json", snapshot
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
