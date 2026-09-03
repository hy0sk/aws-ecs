# app-infra/outputs.tf
# db_endpoint는 RDS가 이 폴더로 이동하면서 base-infra/outputs.tf에서 옮겨왔습니다.

output "db_endpoint" {
  description = "RDS MySQL 데이터베이스 접속 주소"
  value       = aws_db_instance.my_db.endpoint
}

output "alb_dns_name" {
  description = "ALB 자체 주소 (디버깅용 - 실제 서비스 접속은 도메인으로 하세요)"
  value       = aws_lb.my_alb.dns_name
}
