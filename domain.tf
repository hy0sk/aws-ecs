# 1. Route 53에 'hy0sk.cloud' 호스팅 영역(내 땅) 생성
resource "aws_route53_zone" "my_zone" {
  name = "hy0sk.cloud"
}

# 2. AWS가 할당해준 네임서버(NS) 4개 주소 출력하기
output "name_servers" {
  description = "도메인 구매처에 입력할 AWS 네임서버 4개"
  value       = aws_route53_zone.my_zone.name_servers
}
# 3. ACM(SSL 인증서) 발급 요청
resource "aws_acm_certificate" "my_cert" {
  domain_name       = "hy0sk.cloud"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}
  
# 4. Route 53에 인증서 검증용 레코드 추가 (내가 진짜 도메인 주인임을 증명)
resource "aws_route53_record" "cert_validation" {
  for_each = {
    for dvo in aws_acm_certificate.my_cert.domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      record = dvo.resource_record_value
      type   = dvo.resource_record_type
    }
  }

  allow_overwrite = true
  name            = each.value.name
  records         = [each.value.record]
  ttl             = 60
  type            = each.value.type
  zone_id         = aws_route53_zone.my_zone.zone_id
}

# 5. 테라폼아, 인증서 검증 끝날 때까지 기다려!
resource "aws_acm_certificate_validation" "my_cert_val" {
  certificate_arn         = aws_acm_certificate.my_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}

