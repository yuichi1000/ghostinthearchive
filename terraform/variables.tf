# Variables for Ghost in the Archive infrastructure

variable "project_id" {
  description = "Google Cloud Project ID"
  type        = string
}

variable "region" {
  description = "Google Cloud region"
  type        = string
  default     = "asia-northeast1"
}

variable "domain" {
  description = "Primary domain name"
  type        = string
}

variable "admin_subdomain" {
  description = "Admin subdomain"
  type        = string
  default     = "admin"
}

variable "github_repo" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
}

# Web Public Environment Variables (passed to Cloud Build as substitutions)
variable "next_public_gtm_id" {
  description = "Google Tag Manager ID"
  type        = string
  default     = ""
}

variable "next_public_firebase_api_key" {
  description = "Firebase API Key"
  type        = string
}

variable "next_public_firebase_auth_domain" {
  description = "Firebase Auth Domain"
  type        = string
}

variable "next_public_firebase_project_id" {
  description = "Firebase Project ID"
  type        = string
}

variable "next_public_firebase_storage_bucket" {
  description = "Firebase Storage Bucket"
  type        = string
}

variable "next_public_firebase_messaging_sender_id" {
  description = "Firebase Messaging Sender ID"
  type        = string
}

variable "next_public_firebase_app_id" {
  description = "Firebase App ID"
  type        = string
}
