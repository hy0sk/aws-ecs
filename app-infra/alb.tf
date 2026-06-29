# alb.tf

# 1. 로드밸런서(ALB)의 보안 그룹 (방화벽)
resource "aws_security_group" "alb_sg" {
  name        = "my-alb-sg"
  description = "Security group for ALB"
  vpc_id      = data.aws_vpc.default.id # 형석님의 기본 VPC 환경에 맞춤!

  # HTTP(80) 포트 허용
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS(443) 포트 허용 (자물쇠용!)
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 2. 로드밸런서 (ALB) 본체 생성
resource "aws_lb" "my_alb" {
  name               = "my-web-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id]
  subnets            = data.aws_subnets.default.ids # 형석님의 기본 서브넷 환경에 맞춤!
}

# 3. 타겟 그룹 (에러의 원인이었던 그 녀석! my_tg)
resource "aws_lb_target_group" "my_tg" {
  name        = "my-web-tg"
  port        = 80
  protocol    = "HTTP"
  vpc_id      = data.aws_vpc.default.id
  target_type = "ip"

  health_check {
    path                = "/"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
    matcher             = "200"
  }
}

# 4. HTTP(80) 리스너: HTTP로 들어오면 강제로 HTTPS로 튕겨냄 (보안 강화!)
resource "aws_lb_listener" "my_listener" {
  load_balancer_arn = aws_lb.my_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type = "redirect"

    redirect {
      port        = "443"
      protocol    = "HTTPS"
      status_code = "HTTP_301"
    }
  }
}

# 5. HTTPS(443) 리스너: 자물쇠 달고 들어온 사람들을 타겟 그룹으로 전달
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.my_alb.arn
  port              = "443"
  protocol          = "HTTPS"
  ssl_policy        = "ELBSecurityPolicy-2016-08"
  certificate_arn   = data.terraform_remote_state.base.outputs.cert_arn # domain.tf의 인증서 연결!

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.my_tg.arn
  }
}
# 안쪽 폴더의 app-infra/alb.tf 맨 밑에 추가
resource "aws_route53_record" "www" {
  # 👇 수정된 부분: 바깥 폴더의 outputs에서 zone_id를 가져옴!
  zone_id = data.terraform_remote_state.base.outputs.zone_id
  name    = "hy0sk.cloud"
  type    = "A"

  alias {
    name                   = aws_lb.my_alb.dns_name
    zone_id                = aws_lb.my_alb.zone_id
    evaluate_target_health = true
  }
}
