# outputs.tf (바깥 폴더)
output "cert_arn" {
  description = "발급받은 ACM 인증서의 ARN (app-infra에서 가져다 쓸 예정)"
  value       = aws_acm_certificate.my_cert.arn
}
# 바깥 폴더의 outputs.tf 맨 밑에 추가
output "zone_id" {
  description = "Route 53 호스팅 영역 ID"
  value       = aws_route53_zone.my_zone.zone_id
}
# (outputs.tf 파일 맨 밑에 추가)
output "db_endpoint" {
  description = "RDS MySQL 데이터베이스 접속 주소"
  value       = aws_db_instance.my_db.endpoint
}