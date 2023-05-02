import json

import pytest
from FilterAvailableSoftwareImages import SoftwareVersion

version_kwargs = {
    "hostid": "1",
    "filename": "whatever",
    "size": 1,
    "size_kb": 1,
    "release_notes": "whatever",
    "downloaded": False,
    "current": False,
    "latest": False,
    "uploaded": False
}


@pytest.mark.parametrize(
    'left_image_version, right_image_version, expected', [
        # Valid targets
        ("9.1.3", "9.1.2", "9.1.3"),
        ("10.0.3", "9.1.2", "10.0.3"),
        # More than one major release
        ("10.1.3", "9.1.2", None),
        ("10.2.0", "10.0.1", None),
        # left is older than right
        ("9.1.1", "9.1.2", None),
        ("9.0.14", "10.0.11", None),
    ]
)
def test_check_versions(left_image_version, right_image_version, expected):
    from FilterAvailableSoftwareImages import check_versions
    result = check_versions(left_image_version, right_image_version)
    assert result == expected


@pytest.mark.parametrize(
    'current_version, available_images, expected', [
        (
                "9.1.1",
                [
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                    SoftwareVersion(version="9.1.0", **version_kwargs),
                ],
                [
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                ],
        ),
        (
                "9.0.11",
                [
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                ],
                [
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                ],
        ),
    ]
)
def test_trim_by_is_upgrade(current_version, available_images, expected):
    from FilterAvailableSoftwareImages import trim_by_is_upgrade
    result = trim_by_is_upgrade(current_version, available_images)
    assert result == expected


@pytest.mark.parametrize(
    'current_version, available_images, expected', [
        (
                "9.0.11",
                [
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                ],
                [
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                ],
        ),
    ]
)
def test_trim_by_is_upgrade_any_version(current_version, available_images, expected):
    from FilterAvailableSoftwareImages import trim_by_is_upgrade
    result = trim_by_is_upgrade(current_version, available_images, any_version_jump=True)
    assert result == expected


@pytest.mark.parametrize(
    'current_version, target_version, available_images, expected', [
        # two major version upgrade

        (
                "9.1.1",
                "10.1.11",
                [
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                    SoftwareVersion(version="9.1.0", **version_kwargs),
                ],
                [
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                ],
        ),
        # Four major version upgrade
        (
                "8.1.1",
                "10.1.11",
                [
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                    SoftwareVersion(version="9.1.0", **version_kwargs),
                    SoftwareVersion(version="9.0.14", **version_kwargs),
                    SoftwareVersion(version="9.0.1", **version_kwargs),
                ],
                [
                    SoftwareVersion(version="9.0.14", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                ],
        ),
        # upgrade not to latest
        (
                "9.1.3",
                "10.1.11",
                [
                    SoftwareVersion(version="10.1.13", **version_kwargs),
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="9.1.4-h2", **version_kwargs),
                ],
                [
                    SoftwareVersion(version="10.0.11", **version_kwargs),
                    SoftwareVersion(version="10.1.11", **version_kwargs),
                ],
        )
    ]
)
def test_calculate_upgrade_path(current_version, target_version, available_images, expected):
    from FilterAvailableSoftwareImages import calculate_upgrade_path
    result_path = []
    calculate_upgrade_path(current_version, target_version, available_images, result_path)
    assert result_path == expected


def test_main():
    pytest.skip("Might contain sensitive data. To run this unit test, copy output from pan-os-available-software.")
    available_images = json.load(open("test_data/all_available_software.json"))
    installed_images = json.load(open("test_data/installed_images.json"))
    from FilterAvailableSoftwareImages import main
    result = main(installed_images, available_images)
    print(result)