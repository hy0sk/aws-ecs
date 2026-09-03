# app-infra/variables.tf

variable "db_username" {
  description = "RDS 관리자 계정 이름"
  type        = string
  default     = "admin"
}

variable "db_password" {
  description = "RDS 관리자 비밀번호. 코드에 직접 쓰지 말고 terraform.tfvars 또는 환경변수(TF_VAR_db_password)로 주입하세요."
  type        = string
  sensitive   = true
}

variable "skip_rds_final_snapshot" {
  description = "true로 하면 RDS destroy 시 스냅샷 없이 즉시 삭제됩니다(데이터 완전 유실). 앱을 껐다 켜는 용도라면 false(기본값)를 권장합니다 - destroy할 때마다 자동으로 최종 스냅샷을 남겨서 다음에 복원할 수 있게 합니다."
  type        = bool
  default     = false
}
