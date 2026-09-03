# app-infra/ecs.tf

resource "aws_ecs_cluster" "my_cluster" {
  name = "my-test-cluster"
}

resource "aws_cloudwatch_log_group" "ecs_log_group" {
  name              = "/ecs/my-test-web-task"
  retention_in_days = 7
}

resource "aws_ecs_task_definition" "my_task" {
  family                   = "my-test-web-task"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn

  container_definitions = jsonencode([
    {
      name      = "my-web-container"
      image     = "714462451891.dkr.ecr.ap-northeast-2.amazonaws.com/my-test-web-repo:latest"
      cpu       = 256
      memory    = 512
      essential = true
      portMappings = [
        {
          containerPort = 80
          hostPort      = 80
          protocol      = "tcp"
        }
      ],
      # RDS가 이제 같은 app-infra 폴더 안에 있으므로 remote_state 대신 직접 참조합니다.
      environment = [
        { name = "DB_HOST", value = replace(aws_db_instance.my_db.endpoint, ":3306", "") },
        { name = "DB_USER", value = var.db_username },
        { name = "DB_PASS", value = var.db_password },
        { name = "DB_NAME", value = aws_db_instance.my_db.db_name }
      ],
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs_log_group.name
          "awslogs-region"        = "ap-northeast-2"
          "awslogs-stream-prefix" = "ecs"
        }
      }
    }
  ])
}

# 보안 그룹: ALB에서 오는 트래픽만 80번 포트로 허용
resource "aws_security_group" "ecs_sg" {
  name        = "ecs-web-sg"
  description = "Allow HTTP inbound traffic for ECS Fargate"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port       = 80
    to_port         = 80
    protocol        = "tcp"
    security_groups = [aws_security_group.alb_sg.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_ecs_service" "my_service" {
  name            = "my-web-service"
  cluster         = aws_ecs_cluster.my_cluster.id
  task_definition = aws_ecs_task_definition.my_task.arn
  desired_count   = 1
  launch_type     = "FARGATE"

  network_configuration {
    subnets          = data.aws_subnets.default.ids
    security_groups  = [aws_security_group.ecs_sg.id]
    assign_public_ip = true
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.my_tg.arn
    container_name   = "my-web-container"
    container_port   = 80
  }
}

# ---------------------------------------------------
# ECS 오토스케일링 (컨테이너 최소 1개, 최대 3개, CPU 기준)
# ---------------------------------------------------

resource "aws_appautoscaling_target" "ecs_target" {
  max_capacity = 3
  min_capacity = 1
  # 하드코딩된 문자열 대신 실제 리소스를 참조해서 이름이 바뀌어도 안전하게 유지
  resource_id        = "service/${aws_ecs_cluster.my_cluster.name}/${aws_ecs_service.my_service.name}"
  scalable_dimension = "ecs:service:DesiredCount"
  service_namespace  = "ecs"
  depends_on         = [aws_ecs_service.my_service]
}

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
    target_value       = 60.0
    scale_in_cooldown  = 60
    scale_out_cooldown = 60
  }
}
