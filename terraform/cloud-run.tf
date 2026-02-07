# Cloud Run service for web-admin

resource "google_cloud_run_v2_service" "web_admin" {
  name     = "web-admin"
  location = var.region

  template {
    service_account = google_service_account.web_admin.email

    containers {
      image = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/web-admin:latest"

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_CLOUD_REGION"
        value = var.region
      }

      env {
        name  = "PUBLIC_SITE_URL"
        value = "https://${var.domain}"
      }

      # Secrets
      env {
        name = "NEXTAUTH_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.nextauth_secret.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_CLIENT_ID"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_oauth_client_id.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "GOOGLE_CLIENT_SECRET"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.google_oauth_client_secret.secret_id
            version = "latest"
          }
        }
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "512Mi"
        }
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 10
    }
  }

  traffic {
    type    = "TRAFFIC_TARGET_ALLOCATION_TYPE_LATEST"
    percent = 100
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.main,
  ]
}

# Allow unauthenticated access (authentication handled by NextAuth)
resource "google_cloud_run_v2_service_iam_member" "web_admin_public" {
  project  = var.project_id
  location = var.region
  name     = google_cloud_run_v2_service.web_admin.name
  role     = "roles/run.invoker"
  member   = "allUsers"
}

# Domain mapping for admin subdomain
resource "google_cloud_run_domain_mapping" "admin" {
  location = var.region
  name     = "${var.admin_subdomain}.${var.domain}"

  metadata {
    namespace = var.project_id
  }

  spec {
    route_name = google_cloud_run_v2_service.web_admin.name
  }

  depends_on = [google_cloud_run_v2_service.web_admin]
}

output "web_admin_url" {
  description = "URL of the web-admin Cloud Run service"
  value       = google_cloud_run_v2_service.web_admin.uri
}
