# Cloud Build configuration

# Cloud Build trigger for web-public (SSG) deployment
resource "google_cloudbuild_trigger" "web_public" {
  name        = "web-public-deploy"
  description = "Build and deploy web-public to Firebase Hosting"

  # Manual trigger (called from translate pipeline)
  # Can also be triggered via API: gcloud builds triggers run web-public-deploy

  source_to_build {
    uri       = "https://github.com/${var.github_repo}"
    ref       = "refs/heads/main"
    repo_type = "GITHUB"
  }

  build {
    step {
      name       = "node:20"
      entrypoint = "npm"
      args       = ["ci"]
      dir        = "web-public"
    }

    step {
      name       = "node:20"
      entrypoint = "npm"
      args       = ["run", "build"]
      dir        = "web-public"
      env = [
        "GOOGLE_CLOUD_PROJECT=${var.project_id}"
      ]
    }

    step {
      name       = "gcr.io/google.com/cloudsdktool/cloud-sdk"
      entrypoint = "bash"
      args = [
        "-c",
        "npm install -g firebase-tools && firebase deploy --only hosting --project ${var.project_id}"
      ]
      dir = "web-public"
    }

    options {
      logging = "CLOUD_LOGGING_ONLY"
    }

    timeout = "600s"
  }

  service_account = google_service_account.cloud_build.id

  depends_on = [google_project_service.apis]
}

# Variable for GitHub repository
variable "github_repo" {
  description = "GitHub repository in format 'owner/repo'"
  type        = string
  default     = "yuichi1000/ghostinthearchive"
}

output "cloud_build_trigger_id" {
  description = "Cloud Build trigger ID for web-public deployment"
  value       = google_cloudbuild_trigger.web_public.trigger_id
}

# Cloud Build trigger for web-public auto-deploy on push to main
resource "google_cloudbuild_trigger" "web_public_on_push" {
  name        = "web-public-auto-deploy"
  description = "Auto deploy web-public on push to main"

  github {
    owner = split("/", var.github_repo)[0]
    name  = split("/", var.github_repo)[1]
    push {
      branch = "^main$"
    }
  }

  included_files = [
    "web-public/**",
    "shared/**",
    "firebase.json",
  ]

  filename = "web-public/cloudbuild.yaml"

  service_account = google_service_account.cloud_build.id

  depends_on = [google_project_service.apis]
}
