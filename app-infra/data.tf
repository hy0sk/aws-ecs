# app-infra/data.tf
#
# ecs.tf, alb.tf, rds.tf 가 공통으로 쓰는 데이터 소스입니다.
# (기존에는 rds.tf 와 ecs.tf에 각각 aws_vpc.default 가 중복 선언되어 있었습니다.
#  같은 폴더 안에서는 동일한 이름의 data 블록을 두 번 선언할 수 없으므로 한 곳으로 모았습니다.)

data "aws_vpc" "default" {
  default = true
}

data "aws_subnets" "default" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default.id]
  }
}
