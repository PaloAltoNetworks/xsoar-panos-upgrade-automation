import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401

if __name__ in ('__main__', '__builtin__', 'builtins'):

    # get the script args, defaults are defined on the script settings
    args = demisto.args()
    integration = args.get('integration')
    field_name = args.get('field')
    instance_name = args.get('instance')
    override = argToBoolean(args.get('override'))

    # find the current field value
    current_value = ''
    incident = demisto.incident()
    if field_name in incident.keys():
        current_value = incident.get(field_name)
    else:
        custom_fields = incident.get('CustomFields')
        if custom_fields and field_name in custom_fields.keys():
            current_value = custom_fields.get(field_name)

    # find the instances of the integration
    instances = demisto.getModules()
    instance_names = []

    for name, data in instances.items():
        if data.get('brand', '') == integration and data.get('state', '') == 'active':
            instance_names.append(name)

    # if a specific instance is requested expilicitly
    if instance_name and instance_name in instance_names:
        instance_names = instance_name
    else:
        # if multiple active instances, join to preserve the default 'using' behavior
        instance_names = ','.join(instance_names)

    if not current_value or override:
        execute_command('setIncident', {field_name: instance_names})


