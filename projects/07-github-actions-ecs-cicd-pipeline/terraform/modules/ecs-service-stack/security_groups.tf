# Rules live on aws_vpc_security_group_*_rule, not inline. Mixing the two
# makes Terraform fight itself. The provider removes the default allow-all
# egress when the group is created with no inline egress.

resource "aws_security_group" "alb" {
  name        = "p07-${var.environment}-alb"
  description = "Public HTTP listener for the p07 ${var.environment} load balancer"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "p07-${var.environment}-alb"
  }
}

resource "aws_security_group" "tasks" {
  name        = "p07-${var.environment}-tasks"
  description = "Web and API tasks for p07 ${var.environment}"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name = "p07-${var.environment}-tasks"
  }
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  # checkov:skip=CKV_AWS_260: Port 80 is the public HTTP listener. This lab has no HTTPS listener.
  for_each = toset(var.allowed_ingress_cidrs)

  security_group_id = aws_security_group.alb.id
  description       = "HTTP from an allowed CIDR"
  cidr_ipv4         = each.value
  ip_protocol       = "tcp"
  from_port         = 80
  to_port           = 80
}

resource "aws_vpc_security_group_egress_rule" "alb_to_web" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Forward HTTP to web tasks"
  referenced_security_group_id = aws_security_group.tasks.id
  ip_protocol                  = "tcp"
  from_port                    = 3000
  to_port                      = 3000
}

resource "aws_vpc_security_group_egress_rule" "alb_to_api" {
  security_group_id            = aws_security_group.alb.id
  description                  = "Forward HTTP to API tasks"
  referenced_security_group_id = aws_security_group.tasks.id
  ip_protocol                  = "tcp"
  from_port                    = 3001
  to_port                      = 3001
}

resource "aws_vpc_security_group_ingress_rule" "tasks_web" {
  security_group_id            = aws_security_group.tasks.id
  description                  = "Web port from the load balancer"
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 3000
  to_port                      = 3000
}

resource "aws_vpc_security_group_ingress_rule" "tasks_api" {
  security_group_id            = aws_security_group.tasks.id
  description                  = "API port from the load balancer"
  referenced_security_group_id = aws_security_group.alb.id
  ip_protocol                  = "tcp"
  from_port                    = 3001
  to_port                      = 3001
}

# No NAT. Tasks use a public IP and reach ECR, SSM, CloudWatch Logs, and
# STS over HTTPS.
resource "aws_vpc_security_group_egress_rule" "tasks_https" {
  security_group_id = aws_security_group.tasks.id
  description       = "HTTPS to AWS APIs used by the task execution role"
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "tcp"
  from_port         = 443
  to_port           = 443
}
