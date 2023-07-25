
from CommonServerPython import *  # noqa: F401

CHECK_PLAYBOOK_NAME = "PAN-OS Network Operations - Check if Device Onboarded"


def set_playbook():
    demisto.executeCommand("setPlaybook", {"name": CHECK_PLAYBOOK_NAME})


def main():
    set_playbook()
    return_results("SLA Breach script completed.")


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
