# 1. 기본 VPC 정보 가져오기 (데이터베이스를 내 땅에 짓기 위해)
data "aws_vpc" "default" {
  default = true
}

# 2. 데이터베이스용 보안 그룹 (방화벽)
# 아주 중요: 외부(해커)에서는 절대 접근 못 하고, 우리 VPC 내부에서만 접근 가능하게 막아둡니다.
resource "aws_security_group" "rds_sg" {
  name        = "my-rds-sg"
  description = "Allow MySQL inbound traffic from VPC only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    # 내 VPC 네트워크 안에서 출발한 트래픽만 허용! (0.0.0.0/0 절대 금지)
    cidr_blocks = [data.aws_vpc.default.cidr_block] 
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 3. AWS RDS (MySQL) 인스턴스 생성
resource "aws_db_instance" "my_db" {
  identifier             = "my-test-db"
  engine                 = "mysql"
  engine_version         = "8.0"
  instance_class         = "db.t3.micro" # ★ 프리티어 무료 사양!
  allocated_storage      = 20            # 최소 용량 20GB
  db_name                = "community_db" # 생성될 기본 데이터베이스 이름
  
  # DB 접속용 아이디와 비밀번호 (실무에서는 이렇게 평문으로 쓰면 혼나지만, 지금은 실습이니 직관적으로!)
  username               = "admin"
  password               = "password1234!" 
  
  parameter_group_name   = "default.mysql8.0"
  
  # ★ 아주 중요한 옵션들
  skip_final_snapshot    = true  # 나중에 destroy 할 때 백업본 안 남기고 쿨하게 삭제 (과금 방지)
  publicly_accessible    = false # 외부 인터넷에서 DB로 직접 접속 절대 불가 (보안 1순위)
  
  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}