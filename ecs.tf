# ecs.tf

# 1. ECS 클러스터 (운동장) 생성
resource "aws_ecs_cluster" "my_cluster" {
  name = "my-test-cluster"
}

# 2. Task Definition (컨테이너 실행 명세서) 생성
resource "aws_ecs_task_definition" "my_task" {
  family                   = "my-test-web-task"
  requires_compatibilities = ["FARGATE"] # 우리가 직접 EC2 서버를 관리할 필요 없는 Fargate 모드 사용!
  network_mode             = "awsvpc"    # Fargate는 무조건 awsvpc 네트워크 모드를 사용해야 합니다.
  cpu                      = 256         # 0.25 vCPU
  memory                   = 512         # 0.5 GB RAM
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn # 방금 1단계에서 만든 출입증 연결

  # 실행할 컨테이너 상세 정보 (JSON 형식)
  container_definitions = jsonencode([
    {
      name      = "my-web-container"
      image     = "735391218724.dkr.ecr.ap-northeast-2.amazonaws.com/my-test-web-repo:latest" # ★ 여기에 어제 복사한 ECR 주소(latest 포함)를 붙여넣으세요! ★
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = 80 # Nginx 기본 포트 (도커 컨테이너 내부 포트)
          hostPort      = 80
          protocol      = "tcp"
        }
      ]
    }
  ])
}
# 3. 내 AWS 계정의 기본 VPC와 서브넷 정보 자동으로 가져오기 (마법의 코드!)
data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}

# 4. 보안 그룹 (컨테이너가 80번 포트로 외부 접속을 받을 수 있게 문 열어주기)
resource "aws_security_group" "ecs_sg" {
  name        = "ecs-web-sg"
  description = "Allow HTTP inbound traffic for ECS Fargate"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"] # 나가는 트래픽은 모두 허용
  }
}

# 5. 대망의 ECS 서비스 (명세서를 보고 진짜 컨테이너를 띄우고 유지하는 매니저)
resource "aws_ecs_service" "my_service" {
  name            = "my-web-service"
  cluster         = aws_ecs_cluster.my_cluster.id
  task_definition = aws_ecs_task_definition.my_task.arn
  desired_count   = 1       # 컨테이너 몇 개 띄울래? (일단 1개!)
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true # 우리가 인터넷으로 접속해야 하니 공인 IP 부여!
  }
  load_balancer {
    target_group_arn = aws_lb_target_group.alb_tg.arn
    container_name   = "my-web-container" # Task Definition에 적었던 내 컨테이너 이름
    container_port   = 80
  }
}
# 6. ALB(로드밸런서) 전용 보안 그룹
resource "aws_security_group" "alb_sg" {
  name        = "alb-web-sg"
  description = "Allow HTTP traffic to ALB"
  vpc_id      = data.aws_vpc.default.id # 2일 차에 부활시킨 기본 VPC 재활용!

  # 외부 인터넷(0.0.0.0/0)에서 들어오는 80번(HTTP) 포트 접속 허용
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # 밖으로 나가는 트래픽은 전부 허용
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
# 7. 타겟 그룹 (로드밸런서가 트래픽을 토스해줄 목적지 명단)
resource "aws_lb_target_group" "alb_tg" {
  name        = "my-ecs-tg"
  port        = 80
  protocol    = "HTTP"
  target_type = "ip" # Fargate는 가상 머신(EC2)이 아니라 IP 단위로 할당되므로 무조건 ip 모드를 씁니다.
  vpc_id      = data.aws_vpc.default.id

  # 헬스 체크 (로드밸런서가 "너 살아있니?" 하고 주기적으로 찔러보는 설정)
  health_check {
    path                = "/"
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 3
    interval            = 30
  }
}

# 8. ALB 본체 (진짜 로드밸런서)
resource "aws_lb" "my_alb" {
  name               = "my-web-alb"
  internal           = false # 외부 인터넷에서 접속할 거니까 false (내부망 전용이면 true)
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb_sg.id] # 아까 1단계에서 만든 ALB 전용 출입문 연결!
  subnets            = data.aws_subnets.default.ids   # 마법의 코드(기본 서브넷) 재활용!
}

# 9. 리스너 (ALB의 귀: "80번 포트로 들어오는 트래픽을 타겟 그룹으로 보내라!")
resource "aws_lb_listener" "my_listener" {
  load_balancer_arn = aws_lb.my_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.alb_tg.arn
  }
}
# ---------------------------------------------------
# ECS 오토스케일링 (Auto Scaling) 설정
# ---------------------------------------------------

# 1. 오토스케일링 타겟 설정 (컨테이너 최소 1개, 최대 3개)
resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity       = 3
  min_capacity       = 1
  resource_id        = "service/my-test-cluster/my-web-service" 
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
}

# 2. 오토스케일링 정책 (CPU 사용량 70% 기준)
resource "aws_appautoscaling_policy" "ecs_cpu_policy" {
  name               = "cpu-autoscaling"
  policy_type        = "TargetTrackingScaling"
  resource_id        = aws_appautoscaling_target.ecs_target.resource_id
  scalable_dimension = aws_appautoscaling_target.ecs_target.scalable_dimension
  service_namespace  = aws_appautoscaling_target.ecs_target.service_namespace

  target_tracking_scaling_policy_configuration {
    predefined_metric_specification {
      predefined_metric_type = "ECSServiceAverageCPUUtilization"
    }
    target_value       = 70.0
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
}