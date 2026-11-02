resource "aws_lb" "this" {
  # checkov:skip=CKV_AWS_91: No access logs. A log bucket is a production step this lab skips.
  # checkov:skip=CKV2_AWS_28: No WAF. This lab does not pay for a web ACL in front of a demo listener.
  # checkov:skip=CKV2_AWS_20: HTTP only. There is no certificate to redirect to.
  name                       = "p07-${var.environment}"
  internal                   = false
  load_balancer_type         = "application"
  security_groups            = [aws_security_group.alb.id]
  subnets                    = [for subnet in aws_subnet.public : subnet.id]
  drop_invalid_header_fields = true

  # Lab teardown has to delete the load balancer. This finding is recorded
  # in docs/iac-scan-findings.md and is not skipped in code.
  enable_deletion_protection = false

  tags = {
    Name = "p07-${var.environment}"
  }
}

resource "aws_lb_target_group" "web" {
  # checkov:skip=CKV_AWS_378: HTTP target group. The listener is HTTP because this lab has no certificate.
  name                 = "p07-${var.environment}-web"
  port                 = 3000
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = aws_vpc.this.id
  deregistration_delay = 30

  health_check {
    path                = "/healthz"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name = "p07-${var.environment}-web"
  }
}

resource "aws_lb_target_group" "api" {
  # checkov:skip=CKV_AWS_378: HTTP target group. The listener is HTTP because this lab has no certificate.
  name                 = "p07-${var.environment}-api"
  port                 = 3001
  protocol             = "HTTP"
  target_type          = "ip"
  vpc_id               = aws_vpc.this.id
  deregistration_delay = 30

  health_check {
    path                = "/health"
    protocol            = "HTTP"
    matcher             = "200"
    interval            = 30
    timeout             = 5
    healthy_threshold   = 2
    unhealthy_threshold = 2
  }

  tags = {
    Name = "p07-${var.environment}-api"
  }
}

resource "aws_lb_listener" "http" {
  # checkov:skip=CKV_AWS_2: HTTP listener. This lab has no domain or ACM certificate.
  # checkov:skip=CKV_AWS_103: TLS policy does not apply to an HTTP listener.
  load_balancer_arn = aws_lb.this.arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn
  }
}

resource "aws_lb_listener_rule" "api" {
  listener_arn = aws_lb_listener.http.arn
  priority     = 10

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.api.arn
  }

  condition {
    path_pattern {
      values = ["/api/*"]
    }
  }
}
