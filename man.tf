provider "aws" {
  region = "ap-northeast-2" # 서울 리전
}

resource "aws_ecr_repository" "my_web_repo" {
  name                 = "my-test-web-repo"
  force_delete = true
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
