resource "aws_cloudfront_origin_access_control" "board_uploads" {
  name                              = "board-uploads-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

resource "aws_cloudfront_distribution" "board_uploads" {
  enabled             = true
  default_root_object = ""

  origin {
    domain_name              = aws_s3_bucket.board_uploads.bucket_regional_domain_name
    origin_id                = "s3-board-uploads"
    origin_access_control_id = aws_cloudfront_origin_access_control.board_uploads.id
  }

  default_cache_behavior {
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "s3-board-uploads"
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }
}

# CloudFront에서만 이 버킷을 읽을 수 있게 허용 (버킷 자체는 계속 비공개)
resource "aws_s3_bucket_policy" "board_uploads" {
  bucket = aws_s3_bucket.board_uploads.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontServicePrincipal"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.board_uploads.arn}/*"
      Condition = {
        StringEquals = {
          "AWS:SourceArn" = aws_cloudfront_distribution.board_uploads.arn
        }
      }
    }]
  })
}

output "upload_cdn_domain" {
  description = "이미지 조회용 CloudFront 도메인"
  value       = aws_cloudfront_distribution.board_uploads.domain_name
}