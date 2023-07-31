Operational testing for PAN-OS for PAN-OS upgrades.
This integration was integrated and tested with version xx of PAN_OS_Upgrade_Assurance

## Configure PAN-OS Assurance Testing on Cortex XSOAR

1. Navigate to **Settings** > **Integrations** > **Servers & Services**.
2. Search for PAN-OS Assurance Testing.
3. Click **Add instance** to create and configure a new integration instance.

    | **Parameter** | **Required** |
    | --- | --- |
    | Panorama IP or Hostname | True |
    | Panorama Username | True |
    | Panorama Password | True |
    | Server Port | False |
    | Trust any certificate (not secure) | False |
    | Use system proxy settings | False |

4. Click **Test** to validate the URLs, token, and connection.

## Commands

You can execute these commands from the Cortex XSOAR CLI, as part of an automation, or in a playbook.
After you successfully execute a command, a DBot message appears in the War Room with the command details.

### pan-os-assurance-run-readiness-checks

***
Runs checks to confirm a PAN-OS firewall is ready to be upgraded.

#### Base Command

`pan-os-assurance-run-readiness-checks`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| firewall_serial | The firewall serial number to run validations against. Use `pan-os-platform-get-system-info if not known`. | Required | 
| check_list | List of tests to run. If not provided, a base set of tests will be run. | Optional | 
| min_content_version | The minimum content version to check for, enables "content_version" check. | Optional | 
| candidate_version | The candidate version to runchecks against. Enables "free_disk_space" check. | Optional | 
| dp_mp_clock_diff | The drift allowed between DP clock and MP clock. Enabled "planes_clock_sync" check. | Optional | 
| ipsec_tunnel_status | Check a specific IPsec - by tunnel name. Tunnel must be up for this check to pass. | Optional | 
| check_session_exists | Check for the presence of a specific connection. Session check format is &lt;source&gt;/destination/destination-port. example: 10.10.10.10/8.8.8.8/443<br/>. | Optional | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| FirewallAssurance.ReadinessCheckResults | Unknown | Readiness check results | 

#### Command example
```!pan-os-assurance-run-readiness-checks firewall_serial=6DF15830EBE327F```
#### Context Example
```json
{
    "FirewallAssurance": {
        "Firewall": "6DF15830EBE327F",
        "ReadinessCheckResults": [
            {
                "Test": "panorama",
                "reason": "[SUCCESS] ",
                "state": true
            },
            {
                "Test": "ntp_sync",
                "reason": "[ERROR] No NTP server configured.",
                "state": false
            },
            {
                "Test": "candidate_config",
                "reason": "[SUCCESS] ",
                "state": true
            },
            {
                "Test": "expired_licenses",
                "reason": "[SUCCESS] ",
                "state": true
            },
            {
                "Test": "ha",
                "reason": "[ERROR] Device is not a member of an HA pair.",
                "state": false
            }
        ]
    }
}
```

#### Human Readable Output

>### Readiness Check Results
>|Test|state|reason|
>|---|---|---|
>| panorama | true | [SUCCESS]  |
>| ntp_sync | false | [ERROR] No NTP server configured. |
>| candidate_config | true | [SUCCESS]  |
>| expired_licenses | true | [SUCCESS]  |
>| ha | false | [ERROR] Device is not a member of an HA pair. |


### pan-os-assurance-run-snapshot

***
Takes a snapshot of the operational state of the system.

#### Base Command

`pan-os-assurance-run-snapshot`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| firewall_serial | The firewall serial number to run validations against. Use `pan-os-platform-get-system-info if not known`. | Required | 
| snapshot_name | The name of the snapshot to take. Defaults to "fw_snapshot". | Optional | 
| check_list | List of tests to run. If not provided, a base set of tests will be run. | Optional | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| File.EntryID | Unknown | The EntryID of the report file. | 
| File.Extension | String | The extension of the report file. | 
| File.Name | String | The name of the report file. | 
| File.Info | String | The info of the report file. | 
| File.Size | Number | The size of the report file. | 
| File.Type | String | The type of the report file. | 

#### Command example
```!pan-os-assurance-run-snapshot firewall_serial=6DF15830EBE327F```
#### Context Example
```json
{
    "File": {
        "EntryID": "111@d0971597-2a3e-4375-8c4f-043d162d8a06",
        "Info": "text/plain",
        "MD5": "a8a4d8e1c18bf547c4b32ee05f50a59e",
        "Name": "fw_snapshot",
        "SHA1": "73b3b749b8f7e30f886a733aa9b7d01ad88254a6",
        "SHA256": "e4d5b3e8a4d38e3ee5a5a188cbc1d91d54519bef03f87be0ee1f5ccf4ddd9fed",
        "SHA512": "e8d38c4f54c22b0c0aa2d7b3e77dd6c7334633b15bf95f288f325601eb641eee8f36129e95f670b1998f64251c697afbba977c8316771996fe2456bed82e1b1b",
        "SSDeep": "96:8fflcsfEIQfjfgifAf58fwGxWUei2BgxC23n1SefKfMfqfRQGQtnCJ/T:+k2i0gxC6n1SerkECt",
        "Size": 6362,
        "Type": "ASCII text"
    }
}
```

#### Human Readable Output



### pan-os-assurance-compare-snapshots

***
Takes a snapshot of the operational state of the system.

#### Base Command

`pan-os-assurance-compare-snapshots`

#### Input

| **Argument Name** | **Description** | **Required** |
| --- | --- | --- |
| left_snapshot_id | The Left (or "first") snapshot to compare. | Required | 
| right_snapshot_id | The right (or "second") snapshot to compare. | Required | 

#### Context Output

| **Path** | **Type** | **Description** |
| --- | --- | --- |
| FirewallAssurance.SnapshotComparisonResult | Unknown | Snapshot comparison results | 
| FirewallAssurance.SnapshotComparisonRawResult | Unknown | The complete snapshot comparison results | 
