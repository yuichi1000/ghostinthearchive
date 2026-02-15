# Cloud Run service for web-admin

resource "google_cloud_run_v2_service" "web_admin" {
  name     = "web-admin"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_INTERNAL_LOAD_BALANCER"

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

      env {
        name  = "NEXTAUTH_URL"
        value = "https://${var.admin_subdomain}.${var.domain}"
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

      env {
        name  = "CURATOR_SERVICE_URL"
        value = google_cloud_run_v2_service.curator.uri
      }

      env {
        name  = "PIPELINE_SERVICE_URL"
        value = google_cloud_run_v2_service.pipeline.uri
      }

      env {
        name  = "CLOUD_BUILD_TRIGGER_ID"
        value = google_cloudbuild_trigger.web_public.name
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


# Cloud Run service for Curator (theme suggestion API)
resource "google_cloud_run_v2_service" "curator" {
  name     = "curator"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.pipelines.email

    containers {
      image   = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/pipelines:latest"
      command = ["python"]
      args    = ["services/curator.py"]

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }

      resources {
        limits = {
          cpu    = "1"
          memory = "1Gi"
        }
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 2
    }

    timeout = "300s"
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


# Cloud Run service for Pipeline (Blog/Podcast)
# NOTE: Separate from Curator because these pipelines run for 10-30 minutes,
# requiring different resource limits (2 CPU, 2Gi), longer timeouts (1800s),
# and always-on CPU allocation (cpu_idle=false). Curator only needs seconds
# with 1 CPU, 1Gi, and request-based CPU allocation.
resource "google_cloud_run_v2_service" "pipeline" {
  name     = "pipeline"
  location = var.region
  ingress  = "INGRESS_TRAFFIC_ALL"

  template {
    service_account = google_service_account.pipelines.email

    containers {
      image   = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/pipelines:latest"
      command = ["python"]
      args    = ["services/pipeline_server.py"]

      ports {
        container_port = 8080
      }

      env {
        name  = "GOOGLE_CLOUD_PROJECT"
        value = var.project_id
      }

      env {
        name  = "GOOGLE_GENAI_USE_VERTEXAI"
        value = "TRUE"
      }

      env {
        name = "DPLA_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.dpla_api_key.secret_id
            version = "latest"
          }
        }
      }

      env {
        name = "NYPL_API_TOKEN"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.nypl_api_token.secret_id
            version = "latest"
          }
        }
      }

      env {
        name  = "CLOUD_BUILD_TRIGGER_ID"
        value = google_cloudbuild_trigger.web_public.name
      }

      resources {
        limits = {
          cpu    = "2"
          memory = "2Gi"
        }
        cpu_idle = false # Background tasks need CPU after response is sent
      }

      startup_probe {
        http_get {
          path = "/health"
        }
        initial_delay_seconds = 5
        period_seconds        = 10
        failure_threshold     = 3
      }
    }

    scaling {
      min_instance_count = 0
      max_instance_count = 3
    }

    timeout = "1800s"
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


output "web_admin_url" {
  description = "URL of the web-admin Cloud Run service"
  value       = google_cloud_run_v2_service.web_admin.uri
}
