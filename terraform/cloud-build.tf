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

  filename = "web-public/cloudbuild.yaml"

  substitutions = {
    _NEXT_PUBLIC_GTM_ID                       = var.next_public_gtm_id
    _NEXT_PUBLIC_FIREBASE_API_KEY             = var.next_public_firebase_api_key
    _NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN          = var.next_public_firebase_auth_domain
    _NEXT_PUBLIC_FIREBASE_PROJECT_ID           = var.next_public_firebase_project_id
    _NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET       = var.next_public_firebase_storage_bucket
    _NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID = var.next_public_firebase_messaging_sender_id
    _NEXT_PUBLIC_FIREBASE_APP_ID               = var.next_public_firebase_app_id
  }

  service_account = google_service_account.cloud_build.id

  depends_on = [google_project_service.apis]
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

  substitutions = {
    _NEXT_PUBLIC_GTM_ID                       = var.next_public_gtm_id
    _NEXT_PUBLIC_FIREBASE_API_KEY             = var.next_public_firebase_api_key
    _NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN          = var.next_public_firebase_auth_domain
    _NEXT_PUBLIC_FIREBASE_PROJECT_ID           = var.next_public_firebase_project_id
    _NEXT_PUBLIC_FIREBASE_STORAGE_BUCKET       = var.next_public_firebase_storage_bucket
    _NEXT_PUBLIC_FIREBASE_MESSAGING_SENDER_ID = var.next_public_firebase_messaging_sender_id
    _NEXT_PUBLIC_FIREBASE_APP_ID               = var.next_public_firebase_app_id
  }

  service_account = google_service_account.cloud_build.id

  depends_on = [google_project_service.apis]
}
