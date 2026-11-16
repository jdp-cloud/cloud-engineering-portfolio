# GitHub setup

Do this after both environments exist and before the first merge to main. The workflows are `.github/workflows/p07-ci.yml`, `p07-build-and-deploy.yml`, and `p07-rollback.yml`. Nothing here is a secret. Role ARNs and the load balancer DNS are variables, and the workflows mask them in the logs.

The deploy roles trust `repo:jdp-cloud/cloud-engineering-portfolio:environment:staging` and `:environment:production`. Those subjects do not include the branch. The environment deployment-branch rule is what keeps a deploy on main. The build job has no environment, so it trusts `repo:jdp-cloud/cloud-engineering-portfolio:ref:refs/heads/main` and reads a repository variable.

## Staging environment

1. Open the repository on GitHub.
2. Settings → Environments → New environment.
3. Name it `staging`. Click Configure environment.
4. Under Deployment branches and tags, choose Selected branches and tags.
5. Add deployment branch or tag rule. Ref type: Branch. Name pattern: `main`. Add the rule.

Do not add required reviewers on staging.

## Production environment

1. Settings → Environments → New environment.
2. Name it `production`. Click Configure environment.
3. Under Deployment branches and tags, choose Selected branches and tags.
4. Add deployment branch or tag rule. Ref type: Branch. Name pattern: `main`. Add the rule.
5. Enable Required reviewers and add `jdp-cloud`.
6. Leave Prevent self-review off.

`jdp-cloud` is the only reviewer, and the same account starts the workflow. Prevent self-review rejects an approval from the user who triggered the run, so a production job started by that account could never be approved. With it off, the job still waits until that approval is clicked. A push to main does not deploy production in the same step as the workflow run.

## Repository variables

Settings → Secrets and variables → Actions → Variables → New repository variable.

| Name | Value |
| --- | --- |
| `AWS_REGION` | `us-east-1`. This is the region in `terraform/bootstrap/main.tf`. It is not a Terraform output. |
| `P07_ECR_PUSH_ROLE_ARN` | Bootstrap output `gha_ecr_push_role_arn`. The build job has no GitHub environment, so this stays a repository variable. |

```bash
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/bootstrap output -raw gha_ecr_push_role_arn
```

## Environment variables

Set these on each environment, with the same names. On the environment page, open Environment variables → Add variable. Do not create them as repository variables. A job with `environment: staging` must read the staging values.

| Name | Staging | Production |
| --- | --- | --- |
| `AWS_DEPLOY_ROLE_ARN` | Bootstrap output `gha_staging_deploy_role_arn` | Bootstrap output `gha_production_deploy_role_arn` |
| `P07_ALB_DNS` | Staging output `alb_dns_name` | Production output `alb_dns_name` |
| `ECS_CLUSTER` | Staging output `cluster_name` (`p07-staging`) | Production output `cluster_name` (`p07-production`) |

```bash
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/bootstrap output -raw gha_staging_deploy_role_arn
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/bootstrap output -raw gha_production_deploy_role_arn
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/envs/staging output -raw alb_dns_name
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/envs/staging output -raw cluster_name
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/envs/production output -raw alb_dns_name
terraform -chdir=projects/07-github-actions-ecs-cicd-pipeline/terraform/envs/production output -raw cluster_name
```

`P07_ALB_DNS` is the hostname only, with no `http://` and no path.

## Branch ruleset

Create this ruleset after the Project 07 pull request is open and `p07-ci` has finished once, and before that pull request is merged. The check name is not in the picker until that run exists.

1. Settings → Rules → Rulesets → New ruleset → New branch ruleset.
2. Ruleset name: `main`. Enforcement status: Active.
3. Leave the bypass list empty.
4. Target branches → Add target → Include default branch. The default branch is `main`.
5. Enable Require a pull request before merging. Set Required approvals to 0.
6. Enable Require status checks to pass.
7. Add the check named `p07-ci-result`.

Require a pull request before merging, even with zero approvals, because a direct push to main does not run a `pull_request` workflow. Without that rule, a push to main skips `p07-ci`.

`p07-ci-result` is the job of that name in the workflow "p07 CI". It runs on every pull request to main, including one that does not change Project 07, so the check does not stay pending. Do not require `changes`, `test`, or `image-scan`. Those are skipped when the pull request does not touch this project, and a skipped required check would block the merge.
