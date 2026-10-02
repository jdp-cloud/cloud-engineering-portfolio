# Third-party notices

## gcp-to-aws-ha-vpn-terraform-module

- **Source:** https://github.com/GoogleCloudPlatform/gcp-to-aws-ha-vpn-terraform-module
- **Version compared:** `main` at commit `b71ba81` (2023-12-28)
- **Copyright:** Copyright 2023 Google LLC
- **License:** Apache License, Version 2.0. A copy is in [`licenses/Apache-2.0-gcp-to-aws-ha-vpn-terraform-module.txt`](licenses/Apache-2.0-gcp-to-aws-ha-vpn-terraform-module.txt). The license is also available at http://www.apache.org/licenses/LICENSE-2.0.
- **Status:** The upstream project says it is "not an official Google project." This project is not affiliated with or endorsed by Google.

### How this project relates to it

This project follows the same overall design as the upstream module: a Google Cloud HA VPN gateway connected to an AWS Transit Gateway through Site-to-Site VPN connections, four IKEv2 tunnels, one BGP interface and peer per tunnel on the Cloud Router, and an external VPN gateway with four interfaces.

No upstream file was copied. A line-by-line comparison of the two codebases found 4 of 324 non-trivial lines in this project that also appear verbatim upstream. All four are Transit Gateway arguments set to `"enable"` (`default_route_table_association`, `default_route_table_propagation`, `dns_support` and `vpn_ecmp_support`). Everything else is written independently. The differences are listed in the README under [What I changed or added](README.md#what-i-changed-or-added).

Because the design is credited to the upstream module, its license notice is kept here, even though no upstream source file is redistributed.

## Google Cloud documentation

The design also follows Google Cloud's tutorial for creating HA VPN connections between Google Cloud and AWS:
https://cloud.google.com/network-connectivity/docs/vpn/tutorials/create-ha-vpn-connections-google-cloud-aws

That documentation is Google's. This project links to it and does not reproduce it.
