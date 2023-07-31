# XSOAR Upgrade Services 

[![license](https://img.shields.io/badge/license-MIT-blue.svg)](./LICENSE) [![support](https://img.shields.io/badge/Support%20Level-Community-yellowgreen)](./SUPPORT.md)
![Test status](https://github.com/PaloAltoNetworks/xsoar-panos-upgrade-automation/actions/workflows/test_and_secrets.yml/badge.svg)
![Release status](https://github.com/PaloAltoNetworks/xsoar-panos-upgrade-automation/actions/workflows/release.yml/badge.svg)

[Installation guide](docs/installation.md)

## Description

An XSOAR content pack for managing PAN-OS Firewall upgrades at scale.

This pack;

 * Starts, monitors, and tests Firewall upgrades from XSOAR
 * Allows you to batch upgrades together and run upgrades in parallel 
 * Calculates upgrade paths and performs intermediary upgrades when moving between major releases
 * Manages active/passive High Availability 
 * Tests the upgrades were successful 

## Dependencies

This pack leverages the excellent [pan-os-python](https://github.com/PaloAltoNetworks/pan-os-python) and 
[pan-os-upgrade-assurance](https://github.com/PaloAltoNetworks/pan-os-upgrade-assurance) libraries to function.

## Demo

[![XSOAR Demo](http://img.youtube.com/vi/uqYXrNPKqkI/0.jpg)](https://www.youtube.com/watch?v=uqYXrNPKqkI "XSOAR Demo Video")

## License
This project is licensed under the MIT License - see the [LICENSE](./LICENSE) file for details

## Support

Support for this project is provided as "best-effort" by Palo Alto Networks. 