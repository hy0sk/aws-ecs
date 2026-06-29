# app-infra/main.tf
provider "aws" {
  region = "ap-northeast-2"
}

# 바깥 폴더(base-infra)의 상태 파일을 몰래 훔쳐보는(?) 마법의 코드
data "terraform_remote_state" "base" {
  backend = "local"
  config = {
    path = "../terraform.tfstate" # 바깥 폴더의 상태 파일 경로
  }
}