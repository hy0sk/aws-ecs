# base-infra/domain.tf
#
# 🔒 여기가 이번 리팩토링의 핵심입니다.
#
# aws_route53_zone 이 destroy → 재생성 되면 AWS가 새 네임서버(NS) 4개를 발급합니다.
# 가비아에 등록해둔 기존 네임서버와 값이 달라지므로, 그 순간 도메인이 먹통이 됩니다.
# 그래서 이 존은 절대로 앱을 내리고 올리는 과정에서 건드리면 안 됩니다.
#
# 1) 물리적으로 app-infra 와 상태 파일(state)을 완전히 분리하고
# 2) lifecycle.prevent_destroy 로 실수로라도 destroy 명령이 먹히지 않게
# 이중으로 안전장치를 걸어둡니다.

resource "aws_route53_zone" "my_zone" {
  name = "hy0sk.cloud"

  lifecycle {
    prevent_destroy = true
  }
}

output "name_servers" {
  description = "가비아(도메인 구매처)에 등록할 AWS 네임서버 4개 - 최초 1회만 등록하면 이후 절대 바뀌지 않습니다"
  value       = aws_route53_zone.my_zone.name_servers
}

# ACM(SSL 인증서) 발급 요청
resource "aws_acm_certificate" "my_cert" {
  domain_name       = "hy0sk.cloud"
  validation_method = "DNS"

  lifecycle {
    create_before_destroy = true
  }
}

# 도메인 소유권 검증용 레코드
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

resource "aws_acm_certificate_validation" "my_cert_val" {
  certificate_arn         = aws_acm_certificate.my_cert.arn
  validation_record_fqdns = [for record in aws_route53_record.cert_validation : record.fqdn]
}
