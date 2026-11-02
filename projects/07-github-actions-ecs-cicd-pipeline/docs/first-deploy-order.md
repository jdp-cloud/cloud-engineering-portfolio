# First deploy order

Terraform is in the repo. Nothing in this project has been applied.

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

## 2. Push the first images

Phase 3 is what will use `p07-gha-ecr-push`. This push uses your own AWS credentials. Build `linux/amd64`. The task definition is `X86_64`, and an Apple Silicon build without `--platform` will not start on Fargate.

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

`APP_VERSION` is not in the task definition. The apps report `dev` until a later deploy sets it. `GREETING` is the SSM parameter `/p07/<environment>/api/GREETING` (`hello`). `/p07/<environment>/api/EXAMPLE_SECRET` is created as the placeholder `replace-me`. Terraform ignores later changes to that value. Set a real value with `aws ssm put-parameter --overwrite` if you want one. Do not put it in the repo.

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

What this teardown removes: the `p07-*` roles (the three GitHub roles and both task execution roles), the ECR repositories `p07-web` and `p07-api`, and the environment stacks (VPC, load balancer, ECS services, log groups, and SSM parameters). The budget is part of bootstrap and is removed with it.

ECS keeps deregistered task definition revisions in `INACTIVE` state. Terraform deregisters them. The verify script does not treat inactive revisions as leftovers.

```bash
cd projects/07-github-actions-ecs-cicd-pipeline
./scripts/teardown-verify.sh
```

The script checks `us-east-1` only. A clean run exits 0 while the OIDC provider is still there.
