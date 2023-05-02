import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
Given two Snapshot files taken by `TakeOperationalSnapshot`, loads them and runs a comparison to determine the differences.
"""


def get_snapshot_data_as_dict(entry_id: str) -> dict:
    """
    Read the data in the original file based on it's EntryID
    """
    try:
        file_info = demisto.getFilePath(entry_id)
    except Exception as e:
        return_error('Failed to get the file path for entry: {} the error message was {}'.format(entry_id, str(e)))

    file_path = file_info['path']

    # open file and read data
    with open(file_path, 'r') as f:
        data = json.load(f)
        return data


def compare_two_dicts(left: dict, right: dict):
    """Compares two dictionaries and returns the differences in values."""
    differences: list[tuple] = []
    for left_k, left_v in left.items():
        right_v = right.get(left_k)
        if right.get(left_k) != left_v:
            differences.append((f"{left_k} - {left_v}", right_v))

    return differences


def remove_dict_keys(l: list[dict], ignore_keys: list[str]):
    """Removes given keys from the dictionaries within the list."""
    if not ignore_keys:
        return l

    new_list = [{k: v for k, v in d.items() if k not in ignore_keys} for d in l]

    return new_list


def compare_tables(left: list, right: list, index_key: str = "id", ignore_keys: list = None, table_id="compare") -> List[dict]:
    """
    Given two tables, compare by keys to look for difference and return the result.
    :param left: Left table
    :param right: Right table
    :param index_key: Key to use as index
    :param ignore_keys: Keys in table dictionary to ignore in comparison
    :param table_id: The string identifier for the table - appears in output
    :param kwargs: Keyword args !no-auto-argument
    """
    differences = []
    if ignore_keys is str:
        ignore_keys = [ignore_keys]

    left = remove_dict_keys(left, ignore_keys)
    right = remove_dict_keys(right, ignore_keys)

    for left_object in left:
        left_value = left_object.get(index_key)
        right_object = next((item for item in right if item.get(index_key) == left_object.get(index_key)),
                            None)
        # Missing Items
        if not right_object:
            differences.append({
                "key": index_key,
                "value": left_value,
                "description": f"{left_value} missing.",
                "table_id": table_id
            })
        # Changed Items
        else:
            if right_object != left_object:
                dict_differences = compare_two_dicts(left_object, right_object)
                s = ", ".join([f"{x} different to {y}" for (x, y) in dict_differences])
                differences.append({
                    "key": index_key,
                    "value": left_object.get(index_key),
                    "description": f"{s}",
                    "table_id": table_id
                })

    return differences


def compare_snapshots(left_entry_id: str, right_entry_id: str):
    left_snapshot = get_snapshot_data_as_dict(left_entry_id)
    right_snapshot = get_snapshot_data_as_dict(right_entry_id)

    all_differences = []
    all_differences += compare_tables(
        left_snapshot.get("routes"), right_snapshot.get("routes"), table_id="routing", index_key="destination"
    )
    all_differences += compare_tables(
        left_snapshot.get("bgp_peers"), right_snapshot.get("bgp_peers"), table_id="bgp", index_key="peer"
    )
    all_differences += compare_tables(
        left_snapshot.get("arp"), right_snapshot.get("arp"), table_id="arp", index_key="mac", ignore_keys=["ttl"]
    )
    total_differences = len(all_differences)

    return {
        "TotalDifferences": total_differences,
        "Differences": all_differences
    }


def main():
    demisto_args = demisto.args()
    left_entry_id = demisto_args.get("left_entry_id")
    right_entry_id = demisto_args.get("right_entry_id")

    outputs = compare_snapshots(left_entry_id, right_entry_id)
    if outputs.get("Differences"):
        readable_output = tableToMarkdown("Differences Between Snapshots", outputs.get("Differences"))
    else:
        readable_output = "No differences found."

    return_results(
        CommandResults(
            outputs=outputs,
            outputs_prefix="CompareSnapshotFiles",
            readable_output=readable_output
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
