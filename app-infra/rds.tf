# app-infra/rds.tf
#
# 💸 비용 절감 대상. 내렸다 다시 올려도 도메인/네임서버엔 전혀 영향 없습니다.
#
# ⚠️ 데이터 유의사항: RDS를 destroy하면 DB 데이터 자체가 사라집니다.
# skip_rds_final_snapshot = false(기본값)로 두면 destroy할 때마다 AWS가 자동으로
# 최종 스냅샷을 남기므로, 나중에 그 스냅샷으로 복원할 수 있습니다.
# 정말로 스냅샷도 필요 없다면 variables.tf 의 skip_rds_final_snapshot 을 true로 바꾸세요.

resource "aws_security_group" "rds_sg" {
  name        = "my-rds-sg"
  description = "Allow MySQL inbound traffic from VPC only"
  vpc_id      = data.aws_vpc.default.id

  ingress {
    from_port   = 3306
    to_port     = 3306
    protocol    = "tcp"
    # 내 VPC 네트워크 안에서 출발한 트래픽만 허용 (0.0.0.0/0 절대 금지)
    cidr_blocks = [data.aws_vpc.default.cidr_block]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_instance" "my_db" {
  identifier        = "my-test-db"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.micro" # 프리티어 무료 사양
  allocated_storage = 20
  db_name           = "community_db"

  username = var.db_username
  password = var.db_password

  parameter_group_name = "default.mysql8.0"

  skip_final_snapshot       = var.skip_rds_final_snapshot
  final_snapshot_identifier = var.skip_rds_final_snapshot ? null : "my-test-db-final-${formatdate("YYYYMMDDhhmmss", timestamp())}"

  publicly_accessible = false # 외부 인터넷에서 DB로 직접 접속 절대 불가

  vpc_security_group_ids = [aws_security_group.rds_sg.id]
}
