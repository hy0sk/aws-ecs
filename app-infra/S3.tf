resource "aws_s3_bucket" "board_uploads" {
  bucket = "hy0sk-board-uploads"
}

resource "aws_s3_bucket_public_access_block" "board_uploads" {
  bucket                  = aws_s3_bucket.board_uploads.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# 브라우저가 presigned URL로 S3에 직접 PUT 업로드하려면 CORS 허용이 필요합니다.
resource "aws_s3_bucket_cors_configuration" "board_uploads" {
  bucket = aws_s3_bucket.board_uploads.id

  cors_rule {
    allowed_methods = ["PUT", "GET"]
    allowed_origins = ["https://hy0sk.cloud"]
    allowed_headers = ["*"]
    max_age_seconds = 3000
  }
}
resource "aws_s3_bucket_lifecycle_configuration" "board_uploads" {
  bucket = aws_s3_bucket.board_uploads.id

  rule {
    id     = "delete-old-uploads"
    status = "Enabled"

    filter {
      prefix = "posts/"
    }

    expiration {
      days = 365   # 1년 지난 이미지는 자동 삭제. 원하시는 기간으로 조정하세요.
    }
  }
}