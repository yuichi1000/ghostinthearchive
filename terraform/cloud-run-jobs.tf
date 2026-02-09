# Cloud Run Jobs for Python pipelines

# Blog creation pipeline
resource "google_cloud_run_v2_job" "blog_pipeline" {
  name     = "blog-pipeline"
  location = var.region

  template {
    template {
      service_account = google_service_account.pipelines.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/pipelines:latest"

        args = ["main.py"]

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

        resources {
          limits = {
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      timeout     = "1800s" # 30 minutes
      max_retries = 1
    }
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.main,
  ]
}

# Translation pipeline
resource "google_cloud_run_v2_job" "translate_pipeline" {
  name     = "translate-pipeline"
  location = var.region

  template {
    template {
      service_account = google_service_account.pipelines.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/pipelines:latest"

        args = ["translate_main.py"]

        env {
          name  = "GOOGLE_CLOUD_PROJECT"
          value = var.project_id
        }

        env {
          name  = "GOOGLE_GENAI_USE_VERTEXAI"
          value = "TRUE"
        }

        # Cloud Build trigger ID for public site rebuild
        env {
          name  = "CLOUD_BUILD_TRIGGER_ID"
          value = google_cloudbuild_trigger.web_public.trigger_id
        }

        resources {
          limits = {
            cpu    = "2"
            memory = "1Gi"
          }
        }
      }

      timeout     = "600s" # 10 minutes
      max_retries = 1
    }
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.main,
  ]
}

# Podcast generation pipeline
resource "google_cloud_run_v2_job" "podcast_pipeline" {
  name     = "podcast-pipeline"
  location = var.region

  template {
    template {
      service_account = google_service_account.pipelines.email

      containers {
        image = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/pipelines:latest"

        args = ["podcast_main.py"]

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
            cpu    = "2"
            memory = "2Gi"
          }
        }
      }

      timeout     = "1800s" # 30 minutes
      max_retries = 1
    }
  }

  depends_on = [
    google_project_service.apis,
    google_artifact_registry_repository.main,
  ]
}
