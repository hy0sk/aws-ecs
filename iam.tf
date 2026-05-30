# iam.tf

# 1. ECS가 AWS 자원을 쓸 수 있게 해주는 역할(Role) 생성
resource "aws_iam_role" "ecs_task_execution_role" {
  name = "my-ecs-task-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

# 2. 방금 만든 역할에 'ECS 기본 실행 권한(ECR에서 이미지 당겨오기, 로그 남기기)'을 부여
resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}