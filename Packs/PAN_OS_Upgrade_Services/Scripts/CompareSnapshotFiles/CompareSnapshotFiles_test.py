import json

import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import pytest
from unittest.mock import Mock


@pytest.mark.parametrize("args,expected", [
    # Matching tables
    (
            {
                "left": [{"key1": "value1"}],
                "right": [{"key1": "value1"}],
            },
            []
    ),
    # Changed Value
    (
            {
                "left": [{"id": 1, "key1": "value1"}, {"id": 2, "key2": "value1"}],
                "right": [{"id": 1, "key1": "value2"}, {"id": 2, "key2": "value1"}],
            },
            [{'description': 'key1 - value1 different to value2',
              'key': 'id',
              'table_id': 'compare',
              'value': 1}
             ]

    ),
    # Missing key
    (
            {
                "left": [{"id": 1, "key1": "value1"}, {"id": 2, "key2": "value1"}],
                "right": [{"id": 2, "key2": "value1"}],
            },
            [{'description': '1 missing.',
              'key': 'id',
              'table_id': 'compare',
              'value': 1}
             ]
    ),
])
def test_compare_tables(args, expected):
    """Check the comparison logic is valid"""
    from CompareSnapshotFiles import compare_tables
    result = compare_tables(args.get("left"), args.get("right"))
    assert result == expected


def test_compare_snapshots(mocker):
    from CompareSnapshotFiles import compare_snapshots

    mock = Mock()
    mock.side_effect = [
        json.load(open("test_data/snapshot_1.json")),
        json.load(open("test_data/snapshot_2.json")),
    ]
    mocker.patch("CompareSnapshotFiles.get_snapshot_data_as_dict", mock)
    result = compare_snapshots("1", "2")
    assert result == {'TotalDifferences': 2, 'Differences': [
        {'key': 'destination', 'value': '192.168.1.0/24', 'description': '192.168.1.0/24 missing.', 'table_id': 'routing'},
        {'key': 'peer', 'value': 'testlab-server', 'description': 'status - Active different to Connect', 'table_id': 'bgp'}]}
