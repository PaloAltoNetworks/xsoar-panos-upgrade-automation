import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

"""
Filters a list of software images to the ones that can be upgraded or downgraded to.
"""

from dataclasses import dataclass
from typing import Union


@dataclass
class SoftwareVersion:
    """
    :param hostid: Host ID
    :param version: software version in Major.Minor.Maint format
    :param filename: Software version filename
    :param size: Size of software in MB
    :param size_kb: Size of software in KB
    :param release_notes: Link to version release notes on PAN knowledge base
    :param downloaded: True if the software version is present on the system
    :param current: True if this is the currently installed software on the system
    :param latest: True if this is the most recently released software for this platform
    :param uploaded: True if the software version has been uploaded to the system
    """
    hostid: str
    version: str
    filename: str
    size: int
    size_kb: int
    release_notes: str
    downloaded: bool
    current: bool
    latest: bool
    uploaded: bool


@dataclass
class UpgradeVersionTarget(SoftwareVersion):
    current_image: str
    target_version: str
    upgrade_path: List[str]
    next_upgrade_version: str


@dataclass
class ScriptResult:
    versions: list[SoftwareVersion]

    _output_prefix = "FilteredSoftwareVersions"
    _title = "Filtered Available Software Versions"

    _result_cls = SoftwareVersion


def check_if_feature_version_update(left_image_version: str, right_image_version: str, any_version_jump: Optional[bool] = False):
    """Checks if the right version is newer but not more than 1 minor release away from the previous"""

    if left_image_version == right_image_version:
        return

    left_major_version = int(left_image_version.split(".")[0])
    right_major_version = int(right_image_version.split(".")[0])

    left_feature_version = int(left_image_version.split(".")[1])
    right_feature_version = int(right_image_version.split(".")[1])

    # If the major release is the same
    if left_major_version == right_major_version:
        # Check the jump is not more than one minor release above, but is still newer than the right image
        if left_feature_version + 1 == right_feature_version:
            return left_image_version
        elif any_version_jump and right_feature_version > left_feature_version:
            return left_image_version


def get_minor_version_as_float(minor_version_str: str):
    minor_version_str = minor_version_str.replace("-h", ".")
    minor_version_str = minor_version_str.replace("-b", ".")
    return float(minor_version_str)


def check_if_minor_version_update(left_image_version: str, right_image_version: str):
    """Checks if the right version is newer but not more than 1 minor release away from the previous"""

    if left_image_version == right_image_version:
        return

    left_major_version = int(left_image_version.split(".")[0])
    right_major_version = int(right_image_version.split(".")[0])

    left_feature_version = int(left_image_version.split(".")[1])
    right_feature_version = int(right_image_version.split(".")[1])

    left_minor_version = left_image_version.split(".")[-1]
    right_minor_version = right_image_version.split(".")[-1]

    if (left_major_version, left_feature_version) == (right_major_version, right_feature_version):
        # Any software images that share the major and feature releases are valid targets.
        if get_minor_version_as_float(left_minor_version) < get_minor_version_as_float(right_minor_version):
            return left_image_version


def check_if_major_version_update(left_image_version: str, right_image_version: str, any_version_jump=False):
    """Checks if the right version is newer but not more than 1 minor release away from the previous"""

    if left_image_version == right_image_version:
        return

    left_major_version = int(left_image_version.split(".")[0])
    right_major_version = int(right_image_version.split(".")[0])

    right_feature_version = int(right_image_version.split(".")[1])
    # If this is a major release jump
    if left_major_version < right_major_version and any_version_jump:
        return left_major_version

    if left_major_version + 1 == right_major_version:
        # Don't skip minor releases in a major jump - 9.2.0 to 10.0.0 OK, 9.2.0 to 10.1.0 NOT OK
        if right_feature_version == 0:
            return left_image_version


def check_versions(left_image_version: str, right_image_version: str, any_version_jump=False):
    """Checks if the right version is newer but not more than 1 minor release away from the previous"""

    if left_image_version == right_image_version:
        return

    if check_if_minor_version_update(left_image_version, right_image_version):
        return left_image_version

    if check_if_feature_version_update(left_image_version, right_image_version, any_version_jump):
        return left_image_version

    if check_if_major_version_update(left_image_version, right_image_version, any_version_jump):
        return left_image_version


def trim_by_is_upgrade(
        current_version: str, available_images: List[SoftwareVersion], any_version_jump: Optional[bool] = False
) -> List[SoftwareVersion]:
    """Filters the available image list to only images that are valid upgrade targets."""
    versions = []
    for image in available_images:
        # Check for any feature version updates first
        if check_if_feature_version_update(current_version, image.version, any_version_jump):
            if image.version not in [x.version for x in versions]:
                versions.append(image)

    if not versions or any_version_jump:
        # If we didn't get any feature release updates, check for major version updates
        for image in available_images:
            # Check for any feature version updates first
            if check_if_major_version_update(current_version, image.version, any_version_jump):
                if image.version not in [x.version for x in versions]:
                    versions.append(image)

    # Finally, also include the minor release upgrades in the list.
    for image in available_images:
        # Check for any feature version updates first
        if check_if_minor_version_update(current_version, image.version):
            if image.version not in [x.version for x in versions]:
                versions.append(image)

    return versions


def calculate_upgrade_path(current_version, target_version: str, available_images: List[SoftwareVersion],
                           path: List[SoftwareVersion]):
    """
    Given a list of possible upgrade target versions, calculate the upgrade path for each one.
    """
    if current_version == target_version:
        return path

    possible_upgrade_versions = trim_by_is_upgrade(current_version, available_images)
    # If the target version is in the list of available versions
    if target_version in [image.version for image in possible_upgrade_versions]:
        path.append(next(image for image in possible_upgrade_versions if target_version == image.version))
        return path

    latest_available_upgrade_version = possible_upgrade_versions[0]
    path.append(latest_available_upgrade_version)
    return calculate_upgrade_path(latest_available_upgrade_version.version, target_version, available_images, path)


def main(installed_images: Union[list, dict], available_images: Union[list, dict],
         **kwargs) -> ScriptResult:
    """
    Given a table containing installed ("current") PAN-OS Software images, compare with available to determine
    which can be upgraded to by looking for newer releases than are currently installed.
    :param installed_images: SoftwareVersion table of current images
    :param available_images: Complete list of available images for the given platform
    :param kwargs: Keyword args !no-auto-argument
    """
    versions = []
    installed_images = argToList(installed_images)

    available_images = argToList(available_images)
    available_images = [SoftwareVersion(**image_dict) for image_dict in available_images]
    # Trim invalid filenames
    available_images = [image for image in available_images if "xfr" not in image.version]

    result_upgrade_target_versions = []
    for installed_image_dict in installed_images:
        installed_image: SoftwareVersion = SoftwareVersion(**installed_image_dict)
        # show all the potential software upgrades, regardless of how far forward they are
        all_software_upgrade_versions = trim_by_is_upgrade(installed_image.version,
                                                           available_images=available_images,
                                                           any_version_jump=True)
        for candidate_version in all_software_upgrade_versions:
            upgrade_path = []
            upgrade_path = calculate_upgrade_path(
                installed_image.version, candidate_version.version,
                all_software_upgrade_versions,
                upgrade_path
            )

            result_upgrade_target_versions.append(
                UpgradeVersionTarget(
                    current_image=installed_image.version,
                    target_version=candidate_version.version,
                    upgrade_path=[image.version for image in upgrade_path],
                    next_upgrade_version=upgrade_path[0].version,
                    **vars(candidate_version),
                )
            )

    return ScriptResult(
        versions=result_upgrade_target_versions
    )


if __name__ in ('__main__', '__builtin__', 'builtins'):
    result = main(**demisto.args())

    dict_result = [vars(x) for x in result.versions]
    readable_output = tableToMarkdown(result._title, dict_result)
    outputs = {
        "Result": dict_result
    }

    command_result = CommandResults(
        outputs_prefix=result._output_prefix,
        outputs=outputs,
        readable_output=readable_output
    )
    return_results(command_result)
