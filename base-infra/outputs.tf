# base-infra/outputs.tf
# app-infra 가 terraform_remote_state 로 가져다 쓰는 값들입니다.
# db_endpoint 는 RDS를 app-infra로 옮기면서 app-infra/outputs.tf 로 이동했습니다.

output "cert_arn" {
  description = "ACM 인증서 ARN (app-infra의 ALB HTTPS 리스너에서 사용)"
  value       = aws_acm_certificate.my_cert.arn
}

output "zone_id" {
  description = "Route 53 호스팅 영역 ID (app-infra의 A레코드에서 사용)"
  value       = aws_route53_zone.my_zone.zone_id
}

output "domain_name" {
  description = "루트 도메인 이름"
  value       = aws_route53_zone.my_zone.name
}
