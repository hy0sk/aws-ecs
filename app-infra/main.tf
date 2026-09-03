# app-infra/main.tf
#
# 💸 이 폴더(app-infra)는 "유동 인프라" 전용입니다.
# 비용 절감을 위해 자유롭게 destroy/apply 해도 되는 자원만 여기 둡니다.
# (ECS, RDS, ALB, IAM, 오토스케일링 등)
#
# base-infra 는 완전히 별도의 상태 파일(state)로 분리되어 있으므로,
# 여기서 `terraform destroy` 를 해도 도메인/네임서버는 전혀 영향받지 않습니다.

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region = "ap-northeast-2"
}

# base-infra 의 상태 파일에서 cert_arn, zone_id 값을 읽어옵니다.
# base-infra 를 S3 백엔드로 옮기면 이 블록도 backend = "s3" 로 맞춰서 바꿔주세요.
data "terraform_remote_state" "base" {
  backend = "local"
  config = {
    path = "../base-infra/terraform.tfstate"
  }
}
