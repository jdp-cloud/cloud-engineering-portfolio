# First deploy order

Terraform is in the repo. Bootstrap is already applied. Staging and production are applied before the first merge to main.

Apply bootstrap, push the first images, then apply staging, then production. Staging and production both need an image digest. They have no default image.

The state bucket `terraform-state-jdpayne` in `us-east-1` already exists. This project does not create it. State keys:

| Stack | Key |
| --- | --- |
| Bootstrap | `github-actions-ecs-cicd/bootstrap/terraform.tfstate` |
| Staging | `github-actions-ecs-cicd/staging/terraform.tfstate` |
| Production | `github-actions-ecs-cicd/production/terraform.tfstate` |

The backend block is in each root's `versions.tf`. It is not in a file named `backend.tf`, because the repo `.gitignore` ignores that filename. `*.tfvars` is gitignored too. Copy the example file and edit the copy.

Terraform 1.10 or newer is required (`use_lockfile`). The AWS provider is pinned to 6.71.0. The lock files include `darwin_arm64` and `linux_amd64`.

## 1. Bootstrap

The GitHub OIDC provider for `https://token.actions.githubusercontent.com` already exists in the account. Bootstrap looks it up with a data source. `create_github_oidc_provider` defaults to false and cannot be set to true. Do not create the provider, and do not import it. It is shared. It is not in this state.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline/terraform/bootstrap
cp terraform.tfvars.example terraform.tfvars
```

Edit `budget_alert_email` in `terraform.tfvars`. Leave `create_github_oidc_provider = false`.

```bash
terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Bootstrap creates the three `p07-gha-*` roles, the `p07-web` and `p07-api` repositories, and the monthly budget. It does not create a VPC.

Bootstrap is already applied (11 resources). The forecast notification added to that budget is a one-resource in-place update on the next `terraform plan`. That update is expected.

### Activate the Project cost allocation tag

The budget filters on `Project=p07-ecs-cicd`. A tag-filtered budget sees no spend until `Project` is an active cost allocation tag.

```bash
aws ce list-cost-allocation-tags --tag-keys Project
```

The key can take up to 24 hours to appear after the first tagged resource exists. When it does:

```bash
aws ce update-cost-allocation-tags-status \
  --cost-allocation-tags-status TagKey=Project,Status=Active
```

This was done on 2026-11-02. `Project` is Status Active. Spend from before that activation is not backfilled into the budget.

## 2. Push the first images

Later pushes use the `p07-gha-ecr-push` role from the build workflow. This first push uses your own AWS credentials, so the task definitions have a digest before that workflow runs. Build `linux/amd64`. The task definition is `X86_64`, and an Apple Silicon build without `--platform` will not start on Fargate.

Tags are immutable. Use a new tag if you push again. The task definition stores the digest, not the tag.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline
TAG="local-$(git rev-parse --short HEAD)"
WEB_URL=$(terraform -chdir=terraform/bootstrap output -raw ecr_web_repository_url)
API_URL=$(terraform -chdir=terraform/bootstrap output -raw ecr_api_repository_url)

aws ecr get-login-password --region us-east-1 \
  | docker login --username AWS --password-stdin "${WEB_URL%%/*}"

docker build --platform linux/amd64 -t "${API_URL}:${TAG}" apps/api
docker build --platform linux/amd64 -t "${WEB_URL}:${TAG}" apps/web
docker push "${API_URL}:${TAG}"
docker push "${WEB_URL}:${TAG}"

API_DIGEST=$(aws ecr describe-images --region us-east-1 \
  --repository-name p07-api --image-ids imageTag="${TAG}" \
  --query 'imageDetails[0].imageDigest' --output text)
WEB_DIGEST=$(aws ecr describe-images --region us-east-1 \
  --repository-name p07-web --image-ids imageTag="${TAG}" \
  --query 'imageDetails[0].imageDigest' --output text)

echo "${API_URL}@${API_DIGEST}"
echo "${WEB_URL}@${WEB_DIGEST}"
```

Put those two `repository@sha256:...` values in the environment `terraform.tfvars` files.

## 3. Staging, then production

Review each plan before apply. Production uses a separate VPC (`10.80.0.0/16`). Staging uses `10.70.0.0/16`. The same digest is fine for the first apply of both.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline/terraform/envs/staging
cp terraform.tfvars.example terraform.tfvars
# Replace api_image and web_image with the digests printed above.

terraform init
terraform plan -out=tfplan
terraform apply tfplan
```

Repeat in `terraform/envs/production` after staging is up.

`APP_VERSION` is not in the task definition. The apps report `dev` until a later deploy sets it. Terraform creates `/p07/<environment>/api/GREETING` as the String `hello` and `/p07/<environment>/api/EXAMPLE_SECRET` as the SecureString placeholder `replace-me`. Both parameters ignore later changes to `value`. Change `GREETING` with `aws ssm put-parameter --overwrite` and a new deployment (the Phase 4 SSM proof). A later apply must not revert it. Do not put a real secret in the repo.

### Verify on first staging deploy

- Both ECS tasks are `RUNNING`, and the running count matches the desired count.
- Both target groups report healthy targets.
- Neither `/p07/staging/web` nor `/p07/staging/api` contains `EACCES` or `EROFS`. That confirms the Fargate volumes for `/tmp` and `/app/.next/cache` are writable by uid 1000. A local read-only container cannot prove the Fargate mount.

```bash
aws ecs describe-services --region us-east-1 --cluster p07-staging \
  --services p07-staging-web p07-staging-api \
  --query 'services[].{name:serviceName,status:status,running:runningCount,desired:desiredCount}'

aws elbv2 describe-target-groups --region us-east-1 \
  --names p07-staging-web p07-staging-api \
  --query 'TargetGroups[].TargetGroupArn' --output text

aws logs filter-log-events --region us-east-1 \
  --log-group-name /p07/staging/web --filter-pattern '?"EACCES" ?"EROFS"'
aws logs filter-log-events --region us-east-1 \
  --log-group-name /p07/staging/api --filter-pattern '?"EACCES" ?"EROFS"'
```

Pass the target group ARNs from the second command to `aws elbv2 describe-target-health --target-group-arn`.

## 4. Before the first merge to main

The deploy workflow on main updates both environments. It reads the live task definition and registers a new revision. It does not create the cluster, the services, or the load balancer. Do these before merging that workflow to main.

Apply production with the same seed digests used for staging. The commands are in section 3.

If `allowed_ingress_cidrs` was narrowed to your IP, remove that line from `terraform.tfvars` and apply. Do this in staging and in production if both were narrowed. With the line removed, the variable uses its default, `0.0.0.0/0`. GitHub-hosted runners are not on a home IP, and the smoke test calls the load balancer from the runner.

Apply the bootstrap update that adds `ecr:DescribeImages` on the two deploy roles before using rollback with an image tag. The next bootstrap plan shows an in-place change on each deploy role policy. The forecast notification on the budget, if it is still pending, is the separate update described in section 1. Rolling back to the previous revision does not need `DescribeImages`.

Set up the GitHub environments, variables, and the main branch ruleset in `docs/github-setup.md`.

## Teardown

Destroy production, then staging, then bootstrap.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline/terraform/envs/production
terraform destroy

cd ../staging
terraform destroy

cd ../../bootstrap
terraform destroy
```

The GitHub OIDC provider is expected to remain. It is shared and pre-existing, it is not in this state, and `terraform destroy` on bootstrap does not delete it. Do not delete it by hand as part of this teardown.

What this teardown removes: the `p07-*` roles (the three GitHub roles and both task execution roles), the ECR repositories `p07-web` and `p07-api`, and the environment stacks (VPC, load balancer, ECS services, log groups, and SSM parameters). The budget is part of bootstrap and is removed with it. Task definition revisions stay `ACTIVE` until the commands printed by the verify script are run.

Both task definitions set `skip_destroy`. Terraform leaves revisions `ACTIVE` so a rollback can still use them, and so a replace does not deregister revision 1. `scripts/teardown-verify.sh` lists any `ACTIVE` `p07-*` revisions that remain and prints `deregister-task-definition` and `delete-task-definitions` commands. The script does not run those commands.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline
./scripts/teardown-verify.sh
```

The script checks `us-east-1` only. A clean run exits 0 while the OIDC provider is still there.
