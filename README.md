# Jacques Payne | Cloud Engineering Portfolio

![AWS](https://img.shields.io/badge/AWS-Cloud-FF9900?logo=amazonaws&logoColor=white)
![Terraform](https://img.shields.io/badge/Terraform-IaC-7B42BC?logo=terraform&logoColor=white)
![Kubernetes](https://img.shields.io/badge/Kubernetes-GitOps-326CE5?logo=kubernetes&logoColor=white)
![Jenkins](https://img.shields.io/badge/Jenkins-CI%2FCD-D24939?logo=jenkins&logoColor=white)
![Focus](https://img.shields.io/badge/focus-cloud%20security-B71C1C)
[![Secret scan](https://github.com/jdp-cloud/cloud-engineering-portfolio/actions/workflows/gitleaks.yml/badge.svg)](https://github.com/jdp-cloud/cloud-engineering-portfolio/actions/workflows/gitleaks.yml)

Hands-on cloud infrastructure, automation, Kubernetes, CI/CD, and security projects developed as part of my transition from regulated life-sciences operations into cloud engineering. I am targeting **Senior Cloud Security Engineer** roles.

[LinkedIn](https://www.linkedin.com/in/jacques-payne-1ba7b43) | [GitHub](https://github.com/jdp-cloud)

## Start here

Each project has its own README with an at-a-glance summary, architecture, validation steps and evidence. If you have two minutes, read the summary table at the top of one.

| # | Project | What it shows | Technologies | Status |
| --- | --- | --- | --- | --- |
| 01 | [Kubernetes Stateful Application](projects/01-kubernetes-stateful-application/) | A stateful workload with persistent storage, runtime secrets and a non-root security context, with data proven to survive pod replacement | Kubernetes, Minikube, StatefulSet, Splunk | Complete (validated locally) |
| 02 | [Argo CD GitOps and RBAC](projects/02-argocd-gitops/) | Git-driven deployment, drift self-healing, environment boundaries and least-privilege access, with real allow and deny tests | Argo CD, AppProject, Kubernetes RBAC | Complete (validated locally) |
| 03 | [Multi-Region Hub-and-Spoke SIEM](projects/03-multi-region-siem-hub-spoke/) | A seven-region AWS network with centralized log collection, no SSH access and least-privilege security groups | Terraform, AWS Transit Gateway, ALB, Loki, Grafana | Code complete. AWS deployment evidence pending. |

### In progress

- **AWS infrastructure CI/CD:** Terraform deployment through a Jenkins pipeline with infrastructure validation, an approval gate, automated security testing (PortSwigger Dastardly) and teardown
- **Kubernetes platform work:** ingress, TLS with cert-manager, and Splunk on Kubernetes
- **Kubernetes policy and gateways:** OPA, Flux and Kong labs

## Skills demonstrated

| Area | Where to see it |
| --- | --- |
| Infrastructure as Code (modules, provider aliases, remote state) | Project 03 |
| Network security (Transit Gateway routing, security groups, no SSH) | Project 03 |
| Kubernetes workloads and storage | Project 01 |
| GitOps and policy boundaries | Project 02 |
| Access control and least privilege | Projects 02 and 03 |
| Secrets handling (kept out of Git) | Projects 01 and 02 |
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

## Certifications

- AWS Certified Solutions Architect – Associate
- AWS Certified Machine Learning Engineer – Associate
- Oracle Cloud Infrastructure Generative AI Professional
- HashiCorp Terraform Associate – In Progress

## Background

I bring more than 15 years of experience in regulated life-sciences operations, including risk management, audit readiness, vendor oversight, documented controls, and cross-functional delivery.

My current focus is building and documenting hands-on cloud infrastructure skills that can be demonstrated directly through the projects in this repository.
