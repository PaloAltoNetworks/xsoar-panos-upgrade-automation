import demistomock as demisto  # noqa: F401
from CommonServerPython import *  # noqa: F401
import paramiko
import logging

"""
Prepares a Palo Alto NGFW for onboarding by configuring it to connect to Panorama.
"""
DEFAULT_PAN_USERNAME = "admin"
DEFAULT_PAN_PASSWORD = "admin"


def expect(shell, expect):
    out = b''
    # sleep is essential, recv_ready returns False without sleep
    time.sleep(1)
    while shell.recv_ready():
        out += shell.recv(2048)

    if out.decode().find(expect) != -1:
        return

    raise DemistoException(f"Expected {expect}, got {out.decode()}")


def ssh_configure_admin(
        hostname, new_password, default_pan_username=DEFAULT_PAN_USERNAME, default_pan_password=DEFAULT_PAN_PASSWORD
):
    """
    Since 10.x, new firewalls require changing the administrative password before they can be used.
    This function uses paramiko to set a new password.
    """
    # create an ssh client object
    client = paramiko.SSHClient()
    logging.getLogger("paramiko").setLevel(logging.ERROR)
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # connect to the remote server with the old password
    try:
        client.connect(hostname, username=default_pan_username, password=default_pan_password, timeout=5)
    except paramiko.ssh_exception.AuthenticationException:
        # If it fails, try again with the new password incase this script is being re-run.
        client.connect(hostname, username=default_pan_username, password=new_password, timeout=5)

    # invoke an shell
    shell_obj = client.invoke_shell()

    # get the shell output, get the complete output with the while loop
    out = b''
    # sleep is essential, recv_ready returns False without sleep
    time.sleep(1)

    while shell_obj.recv_ready():
        out += shell_obj.recv(2048)

    added = False

    if out.decode().find("Enter old password") != -1:
        shell_obj.send(DEFAULT_PAN_PASSWORD + "\n")
        expect(shell_obj, "Enter new password")
        shell_obj.send(new_password + "\n")
        expect(shell_obj, "Confirm password")
        shell_obj.send(new_password + "\n")
        expect(shell_obj, "Password changed")
        added = True

    client.close()
    return added

def setup_firewall(
        hostname,
        new_password: str,
        default_password=DEFAULT_PAN_PASSWORD,
        default_username=DEFAULT_PAN_USERNAME,
):
    """Sets up the firewall, assuming it has been powered on and is available at `hostname` with the given credentials."""
    added = ssh_configure_admin(hostname, new_password, default_pan_username=default_username, default_pan_password=default_password)

    return {
        "ip": hostname,
        "ssh_password_changed": added
    }


def main():
    args = demisto.args()
    outputs = setup_firewall(
        args.get("hostname"),
        new_password=args.get("new_admin_password"),
    )
    return_results(
        CommandResults(
            outputs_prefix="SetupFirewallFirstLogin",
            outputs=outputs,
            readable_output=tableToMarkdown("Configured For First Login", outputs)
        ))


if __name__ in ('__main__', '__builtin__', 'builtins'):
    main()
