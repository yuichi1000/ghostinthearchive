# Variables for Ghost in the Archive infrastructure

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
  default     = "ghostinthearchive"
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "asia-northeast1"
}

variable "domain" {
  description = "Primary domain name"
  type        = string
  default     = "ghostinthearchive.ai"
}

variable "admin_subdomain" {
  description = "Admin subdomain"
  type        = string
  default     = "admin"
}
