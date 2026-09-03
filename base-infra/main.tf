# base-infra/main.tf
#
# ⚠️ 이 폴더(base-infra)는 "영구 인프라" 전용입니다.
# 도메인, Route53, ACM 인증서처럼 절대 껐다 켜면 안 되는 자원만 둡니다.
# 비용 절감을 위해 내렸다 올렸다 할 자원(ECS, RDS, ALB 등)은 ../app-infra 를 사용하세요.
#
# 운영 규칙: 이 폴더에서는 원칙적으로 `terraform destroy`를 실행하지 않습니다.
# (Route53 존은 lifecycle.prevent_destroy 로 실수 삭제를 막아두었습니다 - domain.tf 참고)

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # 로컬 상태파일(terraform.tfstate) 대신 S3 백엔드를 쓰면
  # 노트북을 바꾸거나 팀원이 늘어나도 상태가 안전하게 보존됩니다.
  # 필요할 때 backend.tf.example 을 참고해서 활성화하세요.
}

provider "aws" {
  region = "ap-northeast-2" # 서울 리전
}
