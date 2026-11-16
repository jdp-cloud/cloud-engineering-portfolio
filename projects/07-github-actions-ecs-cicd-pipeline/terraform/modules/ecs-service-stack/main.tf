resource "aws_ecs_cluster" "this" {
  name = "p07-${var.environment}"

  # Off. Two tasks do not justify the Container Insights metric charge.
  # CKV_AWS_65 is recorded in docs/iac-scan-findings.md and is not skipped.
  setting {
    name  = "containerInsights"
    value = "disabled"
  }
}

locals {
  # ECS does not run the Dockerfile HEALTHCHECK. The same command is set here.
  web_health_command = ["CMD", "node", "-e", "fetch('http://127.0.0.1:3000/healthz').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
  api_health_command = ["CMD", "node", "-e", "fetch('http://127.0.0.1:3001/health').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"]
}

resource "aws_ecs_task_definition" "web" {
  # The rollback workflow needs earlier revisions to stay ACTIVE. Without
  # this, Terraform deregisters revision 1 when the task definition is replaced.
  skip_destroy             = true
  family                   = "p07-${var.environment}-web"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn

  # No task_role_arn. The web container does not call AWS APIs.
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  volume {
    name = "tmp"
  }

  volume {
    name = "next-cache"
  }

  container_definitions = jsonencode([
    {
      name                   = "web"
      image                  = var.web_image
      essential              = true
      user                   = "1000"
      readonlyRootFilesystem = true
      stopTimeout            = 15
      linuxParameters = {
        initProcessEnabled = true
      }
      portMappings = [
        {
          containerPort = 3000
          hostPort      = 3000
          protocol      = "tcp"
        }
      ]
      mountPoints = [
        {
          sourceVolume  = "tmp"
          containerPath = "/tmp"
          readOnly      = false
        },
        {
          sourceVolume  = "next-cache"
          containerPath = "/app/.next/cache"
          readOnly      = false
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.web.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "web"
        }
      }
      healthCheck = {
        command     = local.web_health_command
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }
    }
  ])
}

resource "aws_ecs_task_definition" "api" {
  # The rollback workflow needs earlier revisions to stay ACTIVE. Without
  # this, Terraform deregisters revision 1 when the task definition is replaced.
  skip_destroy             = true
  family                   = "p07-${var.environment}-api"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.execution.arn

  # No task_role_arn. ECS injects GREETING and EXAMPLE_SECRET. The process
  # only reads those environment variables.
  runtime_platform {
    operating_system_family = "LINUX"
    cpu_architecture        = "X86_64"
  }

  volume {
    name = "tmp"
  }

  container_definitions = jsonencode([
    {
      name                   = "api"
      image                  = var.api_image
      essential              = true
      user                   = "1000"
      readonlyRootFilesystem = true
      stopTimeout            = 15
      linuxParameters = {
        initProcessEnabled = true
      }
      portMappings = [
        {
          containerPort = 3001
          hostPort      = 3001
          protocol      = "tcp"
        }
      ]
      mountPoints = [
        {
          sourceVolume  = "tmp"
          containerPath = "/tmp"
          readOnly      = false
        }
      ]
      secrets = [
        {
          name      = "GREETING"
          valueFrom = aws_ssm_parameter.greeting.arn
        },
        {
          name      = "EXAMPLE_SECRET"
          valueFrom = aws_ssm_parameter.example_secret.arn
        }
      ]
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.api.name
          awslogs-region        = var.region
          awslogs-stream-prefix = "api"
        }
      }
      healthCheck = {
        command     = local.api_health_command
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 15
      }
    }
  ])
}

resource "aws_ecs_service" "web" {
  # checkov:skip=CKV_AWS_333: Public IP because there is no NAT. Tasks reach ECR, SSM, and CloudWatch over HTTPS.
  name            = "p07-${var.environment}-web"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  enable_execute_command             = false
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 30

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = [for subnet in aws_subnet.public : subnet.id]
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn
    container_name   = "web"
    container_port   = 3000
  }

  # GitHub Actions owns revisions after the first apply. Phase 3 registers a
  # new revision from describe-task-definition output. It does not apply a
  # committed JSON file. Without this, a later terraform apply rolls the
  # service back to the first revision.
  lifecycle {
    ignore_changes = [task_definition]
  }

  depends_on = [
    aws_lb_listener.http,
    aws_iam_role_policy.execution,
  ]
}

resource "aws_ecs_service" "api" {
  # checkov:skip=CKV_AWS_333: Public IP because there is no NAT. Tasks reach ECR, SSM, and CloudWatch over HTTPS.
  name            = "p07-${var.environment}-api"
  cluster         = aws_ecs_cluster.this.id
  task_definition = aws_ecs_task_definition.api.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  enable_execute_command             = false
  deployment_minimum_healthy_percent = 100
  deployment_maximum_percent         = 200
  health_check_grace_period_seconds  = 30

  deployment_circuit_breaker {
    enable   = true
    rollback = true
  }

  network_configuration {
    subnets          = [for subnet in aws_subnet.public : subnet.id]
    security_groups  = [aws_security_group.tasks.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.api.arn
    container_name   = "api"
    container_port   = 3001
  }

  # Same reason as the web service. GitHub Actions owns task definition
  # revisions after the first apply.
  lifecycle {
    ignore_changes = [task_definition]
  }

  depends_on = [
    aws_lb_listener_rule.api,
    aws_iam_role_policy.execution,
  ]
}
