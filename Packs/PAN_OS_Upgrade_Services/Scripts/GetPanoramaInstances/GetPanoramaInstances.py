import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
from typing import Dict, Any
import traceback


def get_panorama_instances() -> Dict[str, Any]:
    """
        Get instances of Panorama integration for SingleSelect field.

        :rtype: ``dict``
        :return: dict with the ids as options for SingleSelect field e.g
        {"hidden": False, "options": sorted(panorama_instance_names)}
    """
    res = demisto.executeCommand("GetInstanceName", {
        "integration_name": "Panorama",
        "return_all_instances": True
    })
    if is_error(res):
        return_error(get_error(res))

    if not res:
        raise DemistoException('Got an empty list object after executing the command !GetPanoramaInstances')

    panorama_instances = res[0].get('Contents', [])

    panorama_instance_names = []
    # panorama_instances is a list of dict(instanceName, integrationName)
    for instance in panorama_instances:
        panorama_instance_names.append(instance.get('instanceName'))

    return {"hidden": False, "options": sorted(panorama_instance_names)}


def main():
    try:
        result = get_panorama_instances()
        return_results(result)

    except Exception as ex:
        demisto.error(traceback.format_exc())  # print the traceback
        return_error(f'Failed to execute GetPanoramaInstances. Error: {str(ex)}')


''' ENTRY POINT '''

if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
