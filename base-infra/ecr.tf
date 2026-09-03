# base-infra/ecr.tf
#
# 도커 이미지 저장소입니다. 스토리지 비용이 GB당 월 몇백 원 수준으로 매우 작기 때문에,
# 앱 인프라를 껐다 켜도 그동안 빌드해둔 이미지가 사라지지 않도록 영구 인프라에 둡니다.
# (app-infra 를 다시 올릴 때 이 저장소의 최신 이미지를 그대로 ECS에 다시 붙일 수 있습니다.)

resource "aws_ecr_repository" "my_web_repo" {
  name                 = "my-test-web-repo"
  force_delete         = true
  image_tag_mutability = "MUTABLE"

  image_scanning_configuration {
    scan_on_push = true
  }
}
