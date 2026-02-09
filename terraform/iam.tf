# Service accounts and IAM configuration

# Service account for web-admin (Cloud Run)
resource "google_service_account" "web_admin" {
  account_id   = "web-admin-sa"
  display_name = "Web Admin Service Account"
}

# Service account for Cloud Run Jobs (pipelines)
resource "google_service_account" "pipelines" {
  account_id   = "pipelines-sa"
  display_name = "Pipelines Service Account"
}

# Service account for Cloud Build
resource "google_service_account" "cloud_build" {
  account_id   = "cloud-build-sa"
  display_name = "Cloud Build Service Account"
}

# IAM roles for web-admin
resource "google_project_iam_member" "web_admin_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.web_admin.email}"
}

resource "google_project_iam_member" "web_admin_run_invoker" {
  project = var.project_id
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.web_admin.email}"
}

resource "google_project_iam_member" "web_admin_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.web_admin.email}"
}

# IAM roles for pipelines
resource "google_project_iam_member" "pipelines_firestore" {
  project = var.project_id
  role    = "roles/datastore.user"
  member  = "serviceAccount:${google_service_account.pipelines.email}"
}

resource "google_project_iam_member" "pipelines_storage" {
  project = var.project_id
  role    = "roles/storage.objectAdmin"
  member  = "serviceAccount:${google_service_account.pipelines.email}"
}

resource "google_project_iam_member" "pipelines_vertex" {
  project = var.project_id
  role    = "roles/aiplatform.user"
  member  = "serviceAccount:${google_service_account.pipelines.email}"
}

resource "google_project_iam_member" "pipelines_secrets" {
  project = var.project_id
  role    = "roles/secretmanager.secretAccessor"
  member  = "serviceAccount:${google_service_account.pipelines.email}"
}

resource "google_project_iam_member" "pipelines_cloudbuild" {
  project = var.project_id
  role    = "roles/cloudbuild.builds.editor"
  member  = "serviceAccount:${google_service_account.pipelines.email}"
}

# IAM roles for Cloud Build
resource "google_project_iam_member" "cloud_build_firebase" {
  project = var.project_id
  role    = "roles/firebase.admin"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

resource "google_project_iam_member" "cloud_build_firestore" {
  project = var.project_id
  role    = "roles/datastore.viewer"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}

resource "google_project_iam_member" "cloud_build_log_writer" {
  project = var.project_id
  role    = "roles/logging.logWriter"
  member  = "serviceAccount:${google_service_account.cloud_build.email}"
}
