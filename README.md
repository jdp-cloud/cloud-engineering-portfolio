# Jacques Payne | Cloud Engineering Portfolio

![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-GitOps-326CE5?logo=kubernetes&logoColor=white)
![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?logo=jenkins&logoColor=white)
![Focus](https://img.shields.io/badge/focus-cloud%20security-B71C1C)
[![Secret scan](https://github.com/jdp-cloud/cloud-engineering-portfolio/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/jdp-cloud/cloud-engineering-portfolio/actions/workflows/gitleaks.yml)

Hands-on cloud infrastructure, automation, Kubernetes, CI/CD, and security projects developed as part of my transition from regulated life-sciences operations into cloud engineering. I am targeting cloud security engineering and AI platform engineering roles.

[LinkedIn](https://www.linkedin.com/in/jacques-payne-1ba7b43) | [GitHub](https://github.com/jdp-cloud)

[![AWS Certified Solutions Architect – Associate, issued Apr 2025, valid through Apr 2028](https://img.shields.io/badge/AWS%20Certified-Solutions%20Architect%20Associate-FF9900)](https://www.credly.com/badges/3a8289fa-4c39-4954-801f-9a3079484eeb/public_url) [![AWS Certified Machine Learning Engineer – Associate, issued Nov 2025, valid through Nov 2028](https://img.shields.io/badge/AWS%20Certified-Machine%20Learning%20Engineer%20Associate-FF9900)](https://www.credly.com/badges/82c5d1cf-0482-4426-92ef-51bdb033300c) [![Oracle Cloud Infrastructure 2025 Certified Generative AI Professional, issued Dec 2025, valid through Dec 2027](https://img.shields.io/badge/Oracle%20Certified-OCI%202025%20Generative%20AI%20Professional-C74634)](https://catalog-education.oracle.com/pls/certview/sharebadge?id=4C8A3CBFEFCE3AB5BB5403DB801A12A274F898F40B5F9C933545107C7A0C5033)

## Start here

Each project has its own README with an at-a-glance summary, architecture, validation steps and evidence. If you have two minutes, read the summary table at the top of one.

| # | Project | What it shows | Technologies | Status |
| --- | --- | --- | --- | --- |
| 01 | [Kubernetes Stateful Application](projects/01-kubernetes-stateful-application/) | A stateful workload with persistent storage, runtime secrets and a non-root security context, with data proven to survive pod replacement | Kubernetes, Minikube, StatefulSet, Splunk | Complete (validated locally) |
| 02 | [Argo CD GitOps and RBAC](projects/02-argocd-gitops/) | Git-driven deployment, drift self-healing, environment boundaries and least-privilege access, with real allow and deny tests | Argo CD, AppProject, Kubernetes RBAC | Complete (validated locally) |
| 03 | [Multi-Region Hub-and-Spoke Web Application with Centralized SIEM](projects/03-multi-region-hub-and-spoke-web-application-with-centralized-siem/) | A seven-region AWS network with centralized log collection, no SSH access and least-privilege security groups | Terraform, AWS Transit Gateway, ALB, Loki, Grafana | Deployed, verified and torn down. Evidence and cost in the project README. |
| 04 | [WAF to Bedrock Threat Correlation to SOAR Pipeline](projects/04-waf-bedrock-threat-correlation-and-soar-pipeline/) | An AWS pipeline that turns WAF logs into scored findings, incidents and reports. Amazon Bedrock only explains. Deterministic code makes every decision, and containment is never automated. Cognito MFA and group-based access protect the API. | Terraform, AWS WAF, Lambda, Bedrock, EventBridge, DynamoDB, Cognito, Python | Deployed, verified and torn down. Based on a class group lab. Evidence is partial and the limitations are listed in the project README. |
| 05 | [GCP to AWS HA VPN with BGP](projects/05-gcp-to-aws-ha-vpn-secure-connectivity/) | Four IPsec tunnels with BGP between a Google Cloud VPC and an AWS Transit Gateway, generated pre-shared keys and private test machines | Terraform, GCP HA VPN, Cloud Router, AWS Transit Gateway, Site-to-Site VPN | Deployed, verified and torn down. Based on a class group lab. |
| 06 | [Local DevSecOps Pipeline with Jenkins](projects/06-jenkins-devsecops-ci-cd-pipeline/) | A 12-stage Jenkins pipeline, configured as code, that builds and tests a small Flask app, then scans it (SonarQube quality gate, gitleaks, Trivy, OWASP ZAP), deploys it to a local container and tears everything down. One run is blocked by Trivy on purpose and the fixed run passed on 2026-10-03 (a later run stopped at the image scan on a base-image package finding, see the project README). | Jenkins, SonarQube, Trivy, gitleaks, OWASP ZAP, Docker Compose, Python | Run, verified and torn down. Based on a class exercise. |

### In progress

- **AWS infrastructure CI/CD:** Terraform deployment through a Jenkins pipeline with infrastructure validation, an approval gate, automated security testing (PortSwigger Dastardly) and teardown
- **Kubernetes platform work:** ingress, TLS with cert-manager, and Splunk on Kubernetes
- **Kubernetes policy and gateways:** OPA, Flux and Kong labs

## Skills demonstrated

| Area | Where to see it |
| --- | --- |
| Infrastructure as Code (modules, provider aliases, remote state) | Project 03 |
| Network security (Transit Gateway routing, security groups, no SSH) | Project 03 |
| Hybrid connectivity (HA VPN, BGP) | Project 05 |
| Kubernetes workloads and storage | Project 01 |
| GitOps and policy boundaries | Project 02 |
| Access control and least privilege | Projects 02, 03 and 04 |
| Event-driven AWS (Lambda, EventBridge, DynamoDB, SNS) | Project 04 |
| Generative AI with guardrails (Bedrock explains, code decides) | Project 04 |
| API authentication and role-based access (Cognito, MFA, API Gateway authorizer) | Project 04 |
| Secrets handling (kept out of Git) | Projects 01 and 02 |
| Secrets handling in Terraform (generated pre-shared keys) | Project 05 |
| CI/CD with Jenkins (pipeline and configuration as code) | Project 06 |
| SonarQube quality gates | Project 06 |
| Trivy (dependency, container image and Terraform scanning) | Project 06 |
| OWASP ZAP (baseline scan of a deployed container) | Project 06 |
| Troubleshooting and evidence-based documentation | All projects |

## How the projects are documented

Every project follows the same pattern, so you can find things quickly:

```text
projects/NN-project-name/
├── README.md      # At a glance, talk track, architecture, validation, scope
├── manifests/     # or terraform/ for infrastructure code
├── notes/         # Troubleshooting write-ups
└── evidence/      # Command output and screenshots
```

Each README states its scope and limitations plainly. These are learning and portfolio projects, and I describe what was actually validated.

## Repository security practices

- **Automated secret scanning.** A [gitleaks](https://github.com/gitleaks/gitleaks) scan runs over the full commit history on every push and pull request, and weekly (see the badge at the top).
- **Nothing sensitive is committed.** Each project's `.gitignore` excludes Terraform state, `*.tfvars`, real backend configuration, keys and secret manifests. Files such as `backend.tf.example` show the shape without real values.
- **Runtime secrets.** The Splunk administrator password is created at deploy time and never stored in Git.
- **Infrastructure-as-code scanning.** [Checkov](https://www.checkov.io/) scans the Terraform and Kubernetes manifests on every push and pull request. It currently reports findings without blocking the build, and the first results are triaged in [docs/iac-scan-findings.md](docs/iac-scan-findings.md).
- **Dependency updates.** Dependabot proposes weekly updates for GitHub Actions and the Terraform provider, and the workflows pin each action to a commit.

## How I use AI

- **In what I build.** Project 04 uses Amazon Bedrock under one rule: deterministic code decides severity, playbooks and compliance results, and the model only writes the explanation. Anything the code cannot evaluate becomes `REVIEW`, and nothing is ever contained automatically.
- **In how I work.** I use an AI assistant to review my work, draft documentation and run checks such as secret and infrastructure scans. I then verify the result with the tools themselves: scanner output, `terraform validate`, and deployments that were applied and destroyed. A claim in a README is either tested or labeled as untested.

## Certifications

- AWS Certified Solutions Architect – Associate
- AWS Certified Machine Learning Engineer – Associate
- Oracle Cloud Infrastructure Generative AI Professional
- HashiCorp Terraform Associate – In Progress

## Background

I bring more than 10 years of experience in regulated life-sciences operations, including risk management, audit readiness, vendor oversight, documented controls, and cross-functional delivery.

My current focus is building and documenting hands-on cloud infrastructure skills that can be demonstrated directly through the projects in this repository.
