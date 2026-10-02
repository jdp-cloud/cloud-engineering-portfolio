# GCP to AWS HA VPN with BGP

![Terraform](https://img.shields.io/badge/Terraform-%E2%89%A51.10-7B42BC?logo=terraform&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-Transit%20Gateway%20%7C%20Site--to--Site%20VPN-FF9900?logo=amazonaws&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google%20Cloud-HA%20VPN%20%7C%20Cloud%20Router-4285F4?logo=googlecloud&logoColor=white)
![Status](https://img.shields.io/badge/status-deployed%2C%20verified%20and%20torn%20down-brightgreen)

Terraform that connects a Google Cloud VPC to an AWS Transit Gateway with four IPsec tunnels and BGP, generates the pre-shared keys instead of storing them, and adds a private test VM on each side for checking the link.

> **Based on a class group lab.** See [Credits](#credits).

> **Scope:** This is a portfolio lab, not a production deployment. It was deployed once on 2026-10-02, verified and destroyed (see [Evidence](#evidence) and [Cost](#cost)). The code also passes `terraform validate` and a Checkov scan. The section [What is proven and what is not](#what-is-proven-and-what-is-not) says exactly what the evidence covers.

## At a glance

| | |
| --- | --- |
| **Problem** | Two clouds need to exchange private traffic without exposing hosts to the internet, and the tunnel secrets must not end up in a repository. |
| **Solution** | HA VPN on the Google side and two Site-to-Site VPN connections on a Transit Gateway on the AWS side. That gives four tunnels with BGP route exchange. Terraform generates the four pre-shared keys. |
| **Infrastructure** | 47 resource blocks in 4 modules: GCP VPC, subnet, HA VPN gateway, Cloud Router, NAT and firewalls. AWS VPC, Transit Gateway and attachment, 2 customer gateways, 2 VPN connections, flow logs and a KMS key. |
| **Code** | About 1,300 lines of Terraform. One environment (`envs/01-ha-vpn`) composes four reusable modules. |
| **Crypto** | IKEv2, AES-256-GCM, SHA2-256, Diffie-Hellman group 20 |
| **Access model** | No public IP or SSH key on either test machine. GCP uses IAP TCP forwarding, AWS uses Session Manager. |
| **Evidence** | One deployment on 2026-10-02: 4 of 4 tunnels established, 4 BGP peers up, cross-cloud ping in both directions, `iperf3` at 1.29 Gbit/s, then a full destroy. Command output is in [`evidence/`](evidence/). |
| **Cost of the run** | About $0.50 to $0.65 for a 28-minute run (an estimate, see [Cost](#cost)) |
| **Skills shown** | Terraform modules and cross-provider data flow, BGP and HA VPN design, secrets handling in Terraform, private-by-default compute, IaC scanning |

## Contents

- [Architecture](#architecture)
- [Security decisions](#security-decisions)
- [Quick start](#quick-start)
- [Validate it works](#validate-it-works)
- [Evidence](#evidence)
- [Cost](#cost)
- [What is proven and what is not](#what-is-proven-and-what-is-not)
- [What I changed or added](#what-i-changed-or-added)
- [IaC scan results](#iac-scan-results)
- [Known limitations](#known-limitations)
- [Credits](#credits)
- [Repository layout](#repository-layout)

## Architecture

```mermaid
flowchart LR
    subgraph GCP["Google Cloud (us-east4)"]
        GVM["Test VM<br/>no external IP"] --- GSN["Subnet 10.240.0.0/24"]
        GSN --- GR["Cloud Router<br/>ASN 65515"]
        GR --- GW["HA VPN gateway<br/>interface 0 and 1"]
        NAT["Cloud NAT<br/>egress only"] --- GSN
        IAP(["IAP TCP forwarding"]) -.-> GVM
    end

    subgraph AWS["AWS (us-east-1)"]
        TGW["Transit Gateway<br/>ASN 65501"] --- VPC["VPC 10.230.0.0/16"]
        VPC --- AVM["Test instance<br/>no public IP, IMDSv2"]
        SSM(["SSM endpoints"]) -.-> AVM
        CGW0["Customer gateway 0"] --- VPN0["VPN connection 0<br/>tunnels 0 and 1"]
        CGW1["Customer gateway 1"] --- VPN1["VPN connection 1<br/>tunnels 2 and 3"]
        VPN0 --- TGW
        VPN1 --- TGW
        FL[("Flow logs<br/>KMS-encrypted")] -.-> VPC
    end

    GW ==="IPsec / IKEv2<br/>4 tunnels, BGP"=== VPN0
    GW ==="IPsec / IKEv2<br/>4 tunnels, BGP"=== VPN1
```

### How the two sides are built

AWS needs the Google gateway addresses before it can create customer gateways, and Google needs AWS's tunnel details before it can build tunnels. There is no dependency cycle, but data flows both ways, so the environment wires the modules in four steps:

1. `gcp-network` creates the HA VPN gateway, which produces two external IP addresses.
2. `aws-network` creates the VPC and the Transit Gateway.
3. `aws-vpn` creates a customer gateway per Google interface and a VPN connection per customer gateway, and outputs each tunnel's outside IP, inside IP and ASN.
4. `gcp-vpn` uses those outputs to create the peer gateway (four interfaces), four tunnels, and a BGP interface and peer on the Cloud Router per tunnel.

Tunnel *n* uses HA VPN interface *n ÷ 2* and AWS peer interface *n*. Each AWS connection supplies two tunnels, so both Google interfaces and both AWS connections carry traffic.

| Setting | Value |
| --- | --- |
| AWS VPC | `10.230.0.0/16` |
| GCP subnet | `10.240.0.0/24` |
| BGP ASNs | AWS Transit Gateway 65501, Google Cloud Router 65515 |
| Tunnel inside ranges | Four `/30` ranges in `169.254.0.0/16`, chosen outside AWS's reserved ranges |
| Regions | AWS `us-east-1`, GCP `us-east4` (both configurable) |

## Security decisions

| Decision | Why |
| --- | --- |
| **Pre-shared keys are generated by Terraform (`random_password`), never typed.** They are 32 characters with a fixed `k` prefix, because AWS allows only `A-Za-z0-9._` and forbids a leading zero. | A key that was never in a file cannot leak from one. The cost is that the keys live in Terraform state, so state must be private and encrypted (see below). |
| **Remote state in S3 with encryption and native locking** (`use_lockfile`, Terraform 1.10 or later). | The state holds the keys. The backend file is git-ignored and only `backend.tf.example` is committed. |
| **Modern IPsec profile.** IKEv2, AES-256-GCM (which carries its own integrity, so phase 2 integrity is omitted), SHA2-256 and DH group 20. | AWS offers CBC fallbacks, and the `crypto` variable documents how to select them for older peers. |
| **No public addresses on test machines.** The GCP VM has no external IP and is reached through IAP, from Google's IAP range only. The AWS instance is reached through Session Manager over VPC endpoints. | No SSH keys, no bastion, nothing open to `0.0.0.0/0`. |
| **GCP VM is hardened:** shielded VM, OS Login, and a dedicated service account with no roles. Outbound installs go through Cloud NAT (egress only). | Limits what a compromised test VM could do. |
| **AWS instance requires IMDSv2** (`http_tokens = "required"`) and an encrypted root volume. | Blocks the common credential-theft path through the metadata service. |
| **Flow logs on both sides.** AWS logs go to a CloudWatch log group encrypted with a customer-managed KMS key and kept 365 days by default. | A tunnel you cannot observe is hard to trust or debug. |
| **Test workloads are optional** (`enable_test_workloads`). | The VPN can be built without any compute. |

## Quick start

Prerequisites: Terraform 1.10 or later, AWS credentials for a sandbox account, a Google Cloud project with billing and credentials for it (Application Default Credentials work), and the AWS and `gcloud` CLIs.

```bash
cd projects/05-gcp-to-aws-ha-vpn-secure-connectivity/envs/01-ha-vpn

# 1. Remote state. Copy the example, then replace the placeholders with your own private, encrypted bucket.
cp backend.tf.example backend.tf

# 2. Your own values. terraform.tfvars is git-ignored.
cp terraform.tfvars.example terraform.tfvars
$EDITOR terraform.tfvars        # gcp_project_id, optional aws_profile

# 3. Review the plan before applying
terraform init
terraform plan -out=vpn.tfplan
terraform apply vpn.tfplan
```

To check the code without any cloud credentials or state bucket:

```bash
terraform init -backend=false
terraform validate
```

Tear down with `terraform plan -destroy -out=destroy.tfplan`, read it, then apply it. A VPN connection and a Transit Gateway attachment bill by the hour while they exist, so destroy the lab when you finish.

## Validate it works

After an apply, `terraform output verify_commands` prints these checks with your values filled in:

| Check | Expected |
| --- | --- |
| `gcloud compute vpn-tunnels list` | All 4 tunnels `ESTABLISHED` |
| `gcloud compute routers get-status` | 4 BGP peers `Established` |
| `aws ec2 describe-vpn-connections` (tunnel telemetry) | All 4 tunnels `UP` |
| Session Manager on the AWS instance, `ping` and `iperf3` to the GCP VM | Replies and throughput |
| IAP SSH to the GCP VM, `ping` and `iperf3` to the AWS instance | Replies and throughput |

These are the expected results. What the 2026-10-02 run actually showed is in [Evidence](#evidence).

## Evidence

One deployment on 2026-10-02 (UTC), in `us-east-1` and `us-east4`, with Terraform v1.16.4. Apply took 12 minutes 30 seconds (64 resources added), the evidence was captured next, and destroy took 7 minutes 12 seconds (64 resources destroyed). From the start of apply to the end of destroy was 28 minutes.

The evidence is **command output saved as text, plus two screenshots of the Google Cloud console.** Account IDs, the Google Cloud project ID, the state bucket, email addresses, session IDs, resource IDs and public IP addresses are masked. Private and link-local addresses are kept. Failed and partial attempts are kept too.

| File | What it shows |
| --- | --- |
| [`00-run-summary.md`](evidence/00-run-summary.md) | Times, versions and masking rules |
| [`01-gcp-vpn-tunnels.txt`](evidence/01-gcp-vpn-tunnels.txt) | All 4 Google tunnels `ESTABLISHED`: "Tunnel is up and running." |
| [`02-gcp-bgp-status.txt`](evidence/02-gcp-bgp-status.txt) | 4 BGP peers `Established`. The router learned `10.230.0.0/16` (the AWS VPC, AS 65501) over all four tunnels, and advertised `10.240.0.0/24` back. |
| [`03a-aws-vpn-telemetry-initial.txt`](evidence/03a-aws-vpn-telemetry-initial.txt) | First AWS reading: **2 of 4 tunnels `UP`**, the other two `DOWN` with "IPSEC IS UP" while BGP was still settling |
| [`03b-aws-vpn-telemetry-final.txt`](evidence/03b-aws-vpn-telemetry-final.txt) | A few minutes later: **4 of 4 `UP`**, each accepting 1 BGP route |
| [`04-cross-cloud-ping.txt`](evidence/04-cross-cloud-ping.txt) | Ping in both directions over private addresses: 4 of 4 packets each way, 0% loss, average 4.4 ms (AWS to GCP) and 4.5 ms (GCP to AWS) |
| [`05-iperf3-aws-to-gcp.txt`](evidence/05-iperf3-aws-to-gcp.txt) | `iperf3`, AWS instance to GCP VM, 10 seconds, one stream: **1.29 Gbit/s**, 1.50 GB transferred |
| [`06-failed-attempts-and-notes.txt`](evidence/06-failed-attempts-and-notes.txt) | A Session Manager attempt that failed without a terminal, the tunnel-settling delay, and a malformed command |
| [`07-teardown-verification.txt`](evidence/07-teardown-verification.txt) | After destroy: 0 VPN connections, Transit Gateways, attachments, tunnels, gateways, routers, VPC endpoints and test machines in either cloud, and 0 resources in state |
| [`08-gcp-console-vpn-tunnels.png`](evidence/08-gcp-console-vpn-tunnels.png) | Screenshot of the Google Cloud console, Cloud VPN tunnels page: all 4 tunnels `Established` with their BGP sessions `established`, and BGP addresses in `169.254.0.x`. Redacted by the author: the project name and the gateway addresses are hidden. |
| [`09-gcp-console-effective-routes.png`](evidence/09-gcp-console-effective-routes.png) | Screenshot of the Google Cloud console, effective routes for the VPC in `us-east4`: four dynamic routes to `10.230.0.0/16` (the AWS VPC), one per tunnel at priority 100, next to the subnet route `10.240.0.0/24` and the default internet route. Redacted by the author: the project name is hidden. |

Notes on what the output shows:

- **The AWS side took a few extra minutes.** Google reported all four tunnels and BGP peers up before AWS did. That is why there are two telemetry captures.
- **Session Manager needed a terminal.** The first attempt from a non-interactive shell failed with "Cannot perform start session: EOF". Under a pseudo-terminal it worked.
- **`iperf3` ran in one direction only.** The Google VM runs a server and the AWS instance was the client. I did not measure the reverse direction.

## Cost

The numbers below are an **estimate**. Real billing lags by a day or more, so I will compare them with Cost Explorer and the Google Cloud billing report once they settle.

**While it runs**, the stack costs about $0.50 to $0.60 per hour.

| Item | Rate | Per hour |
| --- | --- | --- |
| 2 AWS VPN connections | $0.05 each (from the AWS pricing page) | $0.10 |
| 3 Transit Gateway attachments (1 VPC, 2 VPN) | $0.05 each (the VPN rate is from the AWS pricing page) | $0.15 |
| 3 interface VPC endpoints | about $0.01 each (not verified) | $0.03 |
| AWS `t3.micro`, KMS key, flow logs | about $0.012 (not verified) | $0.01 |
| 4 Google HA VPN tunnels | about $0.05 to $0.075 each (not verified, Google's pricing pages did not load) | $0.20 to $0.30 |
| Cloud NAT and the `e2-micro` VM | about $0.012 (not verified) | $0.01 |

**For this run** (28 minutes from the start of apply to the end of destroy):

| Part | Estimate |
| --- | --- |
| AWS hourly-billed items (VPN, Transit Gateway attachments, endpoints), each billed as one hour because a partial hour rounds up | about $0.28 |
| AWS per-second items (instance, KMS key) | under $0.01 |
| Google tunnels (they existed for roughly 10 to 15 minutes, and no more than 28) | $0.04 to $0.14 |
| Google VM and Cloud NAT | under $0.01 |
| Data transfer: 1.5 GB from AWS to Google at about $0.09 per GB, plus Transit Gateway processing at about $0.02 per GB (not verified) | about $0.17 |
| **Total** | **about $0.50 to $0.65** |

Two things remain after the destroy and do not add to the cost. The KMS key is scheduled for deletion, with the 7-day window set in the code, and I understand keys in that state are not billed. The compute and IAP APIs that Terraform enabled stay enabled, because the code sets `disable_on_destroy = false`.

## What is proven and what is not

| Claim | Status |
| --- | --- |
| The configuration is valid Terraform (Terraform v1.16.4, providers aws 6.66.0, google 7.46.1, random 3.9.1) | **Checked.** `init -backend=false` and `validate` pass, and `fmt` is clean. |
| The code follows common IaC security checks | **Checked.** See [IaC scan results](#iac-scan-results). |
| The configuration applies cleanly | **Demonstrated** once. 64 resources were added with no errors. |
| The tunnels establish and BGP exchanges routes | **Demonstrated** once. 4 of 4 Google tunnels `ESTABLISHED`, 4 BGP peers `Established`, the AWS VPC range learned over all four tunnels, and 4 of 4 AWS tunnels `UP` (after the first reading showed 2 of 4). See evidence 01 to 03b. |
| Cross-cloud ping works | **Demonstrated** in both directions, with no packet loss. See evidence 04. |
| Cross-cloud throughput works | **Demonstrated in one direction only**: 1.29 Gbit/s from AWS to Google with one stream for 10 seconds. The reverse direction was not measured. See evidence 05. |
| Clean teardown | **Demonstrated.** Destroy removed 64 resources, and read-only checks found nothing left in either cloud or in state. The KMS key is scheduled for deletion. See evidence 07. |
| Cost of a run | **Estimated, not yet billed.** See [Cost](#cost). |
| Failover when a tunnel is lost | **Not tested.** |

## What I changed or added

This project is my rework of a class group lab and follows the design of Google's [gcp-to-aws-ha-vpn-terraform-module](https://github.com/GoogleCloudPlatform/gcp-to-aws-ha-vpn-terraform-module) (see [Credits](#credits)). I compared this project against both: Google's module and the group lab draft. Each difference below is one I checked in both codebases.

### Compared with Google's module

| Area | Upstream module | This project |
| --- | --- | --- |
| **Pre-shared keys** | Takes one `shared_secret` input and uses it for every tunnel on both clouds. | Generates four different keys with `random_password`, one per tunnel, and passes them to both sides. |
| **IPsec parameters** | Sets none on the AWS connection, so AWS defaults apply. | Sets IKEv2, AES-256-GCM, SHA2-256 and DH group 20 through a `crypto` variable. |
| **BGP inside addresses** | Leaves them for AWS to assign. | Pins four `/30` ranges in `169.254.0.0/16`, chosen outside AWS's reserved ranges. |
| **Peer ASN on the Cloud Router** | A required input (`aws_router_asn`). | Read from each AWS tunnel's output. |
| **Route advertisement** | Custom, advertising all subnets. | Default, which advertises the VPC's subnet ranges. |
| **Transit Gateway attachment** | Uses `awscc_ec2_transit_gateway_attachment`, so it depends on the `awscc` provider. | Uses `aws_ec2_transit_gateway_vpc_attachment`, so only the `aws`, `google` and `random` providers are needed. |
| **Transit Gateway shared attachments** | `auto_accept_shared_attachments = "enable"` | `"disable"` |
| **Number of tunnels** | A `num_tunnels` input, in multiples of 2 with a minimum of 4. | Fixed at four, with validations that enforce the counts. |
| **Networks** | The module takes an existing VPC, subnets and GCP network as inputs. Its example builds networks with the `terraform-aws-modules/vpc` module. | Creates its own networks in the `aws-network` and `gcp-network` modules from plain resources. |
| **Structure** | A flat root module, one network submodule and an example. | One environment root (`envs/01-ha-vpn`) composing four modules. |
| **Authentication** | The example impersonates a Google service account through an access token. | Application Default Credentials for Google (never a downloaded key) and the standard credential chain for AWS, with default tags on AWS resources. |
| **Added here** | None of these exist upstream. | A private test VM and instance, flow logs on both sides (AWS logs use a customer-managed KMS key), SSM endpoints, an IAP firewall rule, Cloud NAT, shielded-VM and OS Login settings, IMDSv2 enforcement and a `verify_commands` output. |
| **Versions and pinning** | Terraform `~> 1.6`, `aws ~> 5.31`, `google ~> 5.10`. No lock file in the repository. | Terraform `>= 1.10`, `aws ~> 6.0`, `google >= 6.0, < 8.0`, `random ~> 3.6`, and a committed lock file with hashes for three platforms. |
| **State** | No backend configuration in any Terraform file. | A documented S3 backend with native locking, shipped as `backend.tf.example`. |

What the two share: the topology (HA VPN gateway, four tunnels, an external gateway with four interfaces, one BGP interface and peer per tunnel), and four identical Transit Gateway settings.

### Compared with the group lab draft

The group lab draft is the group's original Terraform for this lab, kept privately and not published. I read it without changing it. It has five numbered files (authentication, an empty backend file, variables, AWS VPN and GCP VPN).

| Area | Group lab draft | This project |
| --- | --- | --- |
| **Pre-shared keys** | Typed into the Terraform files as literal values, on four AWS tunnel arguments and four Google tunnels. | Generated with `random_password` (four keys) and passed to both sides. No key value is in any file. |
| **AWS-side gateway** | A virtual private gateway attached to a VPC. The files define no subnets and no route tables. | A Transit Gateway with a VPC attachment, a subnet and a route table. |
| **IPsec parameters** | AES-256 with SHA2-256, and a different Diffie-Hellman group on each tunnel (15, 16, 18 and 19). | AES-256-GCM, SHA2-256 and DH group 20 on every tunnel, set through a `crypto` variable. |
| **Tunnels and BGP peers** | Four tunnel blocks, four router interfaces and four peers written out by hand, with the AWS ASN typed into each peer. | Built with `count` from the AWS tunnel outputs, so the peer ASN and addresses come from AWS. |
| **Google authentication** | The provider points at a JSON key file path. | Application Default Credentials, never a downloaded key. |
| **Firewall** | Two firewall rules. One allows UDP 500 and 4500, ESP and ICMP from `0.0.0.0/0`. | No rule in the modules or the environment is open to `0.0.0.0/0`. On the Google side, ingress is limited to the AWS CIDR and Google's IAP range. |
| **Providers** | Declares an `awscc` provider but has no `awscc` resources. No version constraints and no lock file. | Only the `aws`, `google` and `random` providers, with version constraints and a committed lock file for three platforms. |
| **Structure and state** | Five flat files, one environment, and an empty backend file. | One environment root composing four modules, with a documented S3 backend in `backend.tf.example`. |
| **Regions and names** | The AWS region and resource names are fixed in the code. The Google region defaults to `southamerica-west1`. | Regions are variables (defaults `us-east-1` and `us-east4`), and every name starts from a `name_prefix`. |
| **Added here** | None of these exist in the draft. | Private test VM and instance, flow logs on both sides with a customer-managed KMS key, SSM endpoints, IAP access, Cloud NAT and a `verify_commands` output. |

What the draft and this project share: an HA VPN gateway, an external gateway with four interfaces, two customer gateways, two VPN connections, four IKEv2 tunnels, BGP with the same ASNs (AWS 65501 and Google 65515), and one router interface and peer per tunnel.

Pre-shared keys are the change I care most about: the group lab draft had literal pre-shared keys in its Terraform files. This version generates them instead.

## IaC scan results

[Checkov](https://www.checkov.io/) 3.3.22 over this project (Terraform framework): **134 passed, 0 failed, 3 skipped.**

The three skips are inline suppressions, each with its reason in the code:

| Check | Resource | Reason |
| --- | --- | --- |
| `CKV_GCP_38` | Test VM | A disposable lab VM holding no data. Google-managed encryption at rest is enough. Customer-supplied or customer-managed keys are a production step. |
| `CKV_AWS_394` | Availability Zone data source | Only the first AZ name is used, so a newly added zone cannot change the result. |
| `CKV2_AWS_5` | Endpoint security group | It is attached to the SSM interface endpoints through `for_each`, which the check cannot follow. |

## Known limitations

- **One run.** The evidence comes from a single deployment on 2026-10-02. It is saved as masked text output plus two console screenshots, and the throughput test ran in one direction with one stream.
- **Pre-shared keys are in Terraform state.** That is a deliberate trade-off. It is only safe with a private, encrypted state bucket and restricted access. Rotating a key means replacing the `random_password` resource.
- **One environment, one region pair.** There is no staging or production split, and no CI pipeline for plans.
- **One VPC, one subnet per side.** It is a connectivity lab, not a landing zone.
- **Not a full redundancy test.** Four tunnels give two connections on each side, but a failover test (stopping a tunnel and watching BGP converge) has not been run.
- **No traffic inspection.** There is no firewall or inspection appliance between the clouds, only security groups and firewall rules.
- **Costs accrue while it runs.** The VPN connections, Transit Gateway attachment, VPC endpoints and test machines are billed hourly.

## Credits

- **Class lab:** Class 7, Armageddon 1, a group lab (instructor-led). Participants: Jacques Payne (group leader), Joe Tolliver, Jr., Kirk Alton, Cautchy Bailly, Larry Shelton and Xavier Edwards. The group wrote the original lab Terraform. This project is my rework of it.
- **Upstream module:** [GoogleCloudPlatform/gcp-to-aws-ha-vpn-terraform-module](https://github.com/GoogleCloudPlatform/gcp-to-aws-ha-vpn-terraform-module), Copyright 2023 Google LLC, licensed under the Apache License 2.0. This project follows its overall design. I compared against commit `b71ba81` (2023-12-28). The upstream project says it is "not an official Google project", and this project is not affiliated with or endorsed by Google.
- **Google Cloud documentation:** the tutorial for [creating HA VPN connections between Google Cloud and AWS](https://cloud.google.com/network-connectivity/docs/vpn/tutorials/create-ha-vpn-connections-google-cloud-aws).
- **License notice:** the Apache-2.0 attribution and a copy of the license are in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md) and [`licenses/`](licenses/). No upstream file was copied. A line-by-line comparison found only four matching lines, all generic Transit Gateway arguments.

## Repository layout

```text
.
├── README.md
├── envs/
│   └── 01-ha-vpn/        main, variables, outputs, providers, versions, lock file,
│                         terraform.tfvars.example, backend.tf.example, .gitignore
└── modules/
    ├── aws-network/      VPC, Transit Gateway, flow logs, KMS key, SSM endpoints, test instance
    ├── aws-vpn/          customer gateways and VPN connections
    ├── gcp-network/      VPC, subnet, HA VPN gateway, Cloud Router, NAT, firewalls, test VM
    └── gcp-vpn/          peer gateway, tunnels, BGP interfaces and peers
```
