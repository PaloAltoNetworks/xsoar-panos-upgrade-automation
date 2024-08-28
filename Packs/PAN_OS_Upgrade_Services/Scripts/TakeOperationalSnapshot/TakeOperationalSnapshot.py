import demistomock as demisto
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


def get_routing_details(command_args: {}):
    """
    Gets the routing table from the given target
    """
    result = run_command("pan-os-platform-get-routes", command_args)
    if result:
        return result.get("Result", [])
    else:
        return []


def get_bgp_peers(command_args: {}):
    """
    Gets the current BGP neighbor table from the target
    """
    result = run_command("pan-os-platform-get-bgp-peers", command_args)
    if result:
        return result.get("Result", [])
    else:
        return []



def get_arp_tables(command_args: {}):
    """
    Gets the current BGP neighbor table from the target
    """
    result = run_command("pan-os-platform-get-arp-tables", command_args)
    if result:
        return result.get("Result", [])
    else:
        return []



def take_snapshot(target: Optional[str] = None, panos_instance: Optional[str] = None) -> str:
    """
    Takes a snapshot of all the operational state of the PAN-OS target device and returns it as a json string.
    """
    command_args = {}
    if target:
        command_args["target"] = target
    if panos_instance:
        command_args["using"] = panos_instance
    else:
        instances = demisto.getModules()
        i_names = []
        for name, data in instances.items():
            if data.get('brand', '') == 'Panorama' and data.get('state', '') == 'active':
                i_names.append(name)
        command_args["using"] = ','.join(i_names)

    snapshot = {
        "routes": get_routing_details(command_args),
        "bgp_peers": get_bgp_peers(command_args),
        "arp": get_arp_tables(command_args),
    }

    snapshot_json = json.dumps(snapshot)
    return snapshot_json


def main():
    demisto_args = demisto.args()
    target = demisto_args.get("target")
    panos_instance = demisto_args.get("panos_instance", "")

    snapshot = take_snapshot(target, panos_instance)
    # Timestamp the file name
    time_string = int(datetime.now().timestamp())
    return_results(
        fileResult(
            f"{target}_System_Snapshot_{time_string}.json", snapshot
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
