import demistomock as demisto
from CommonServerPython import *  # noqa: F401


"""Given a device host id from the PAN-OS integration creates or updates an existing device incident."""

current_incident_id = demisto.incidents()[0].get("id")
res = demisto.executeCommand("GetIncidentsByQuery", {
    "query": f"-status:closed -category:job type:\"PAN-OS Network Operations - Device\" -type:\"PAN-OS Network Operations - Device Upgrade\""
})
if is_error(res):
    return_error(get_error(res))

new_target = demisto.args().get("target")

incidents = json.loads(res[0]['Contents'])
device_incident_found = False

outputs = {
    "device_incident_id": None,
    "device_incident_link": None
}
human_readable_result = ""

for incident in incidents:
    target = incident.get('CustomFields', {}).get('panosnetworkoperationstarget')
    if target == new_target:
        # If the incident already exists, simply update it by re-running the default playbook
        incident_id = incident.get("id")
        demisto.executeCommand("setPlaybook", {
            "incidentId": incident_id
        })
        human_readable_result = "updated incident " + incident_id
        device_incident_found = True
        outputs = {
            "device_incident_id": incident_id,
            "device_incident_link": f'<a href="/#/incidents/{incident_id}">{incident_id}</a>'
        }

if not device_incident_found:
    # Copy the pan-os instance and set to the defaults if not found
    pan_os = incident.get('CustomFields', {}).get('panosnetworkoperationspanoramainstance', '')
    if not pan_os:
        instances = demisto.getModules()
        i_names = []
        for name, data in instances.items():
            if data.get('brand', '') == 'Panorama' and data.get('state', '') == 'active':
                i_names.append(name)
        pan_os = ','.join(i_names)
    res = demisto.executeCommand("createNewIncident", {
        "name": new_target,
        "type": "PAN-OS Network Operations - Device",
        "panosnetworkoperationstarget": new_target,
        "panosnetworkoperationsparentincidentid": current_incident_id,
        "panosnetworkoperationspanoramainstance": pan_os
    })
    created_incident = res[0]
    created_incident_id = created_incident.get("EntryContext", dict()).get("CreatedIncidentID")
    outputs = {
        "device_incident_id": created_incident_id,
        "device_incident_link": f'<a href="/#/incidents/{created_incident_id}">{created_incident_id}</a>'
    }
    human_readable_result = f"Created new incident {created_incident_id}"

command_result = CommandResults(
    outputs_prefix="DeviceIncidents",
    outputs=outputs,
    readable_output=human_readable_result
)
return_results(command_result)
