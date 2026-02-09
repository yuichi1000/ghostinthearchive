# Terraform outputs

output "dns_zone_name" {
  description = "Name of the DNS zone"
  value       = google_dns_managed_zone.main.name
}

output "artifact_registry_repository" {
  description = "Artifact Registry repository URL"
  value       = "${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive"
}

output "service_accounts" {
  description = "Service account emails"
  value = {
    web_admin   = google_service_account.web_admin.email
    pipelines   = google_service_account.pipelines.email
    cloud_build = google_service_account.cloud_build.email
  }
}

output "cloud_build_push_trigger_id" {
  description = "Cloud Build trigger ID for web-public auto-deploy on push"
  value       = google_cloudbuild_trigger.web_public_on_push.trigger_id
}

output "cloud_run_jobs" {
  description = "Cloud Run Jobs names"
  value = {
    blog      = google_cloud_run_v2_job.blog_pipeline.name
    translate = google_cloud_run_v2_job.translate_pipeline.name
    podcast   = google_cloud_run_v2_job.podcast_pipeline.name
  }
}

output "next_steps" {
  description = "Next steps after terraform apply"
  value       = <<-EOT

    ========================================
    NEXT STEPS
    ========================================

    1. Set secret values:
       See 'secret_setup_instructions' output

    2. Configure Spaceship nameservers:
       Update nameservers to: ${join(", ", google_dns_managed_zone.main.name_servers)}

    3. Build and push Docker images:
       # web-admin
       cd web-admin
       gcloud builds submit --tag ${var.region}-docker.pkg.dev/${var.project_id}/ghostinthearchive/web-admin

       # pipelines
       cd ..
       gcloud builds submit --config cloudbuild-pipelines.yaml .

    4. Deploy web-admin:
       gcloud run services update web-admin --region ${var.region}

    5. Deploy web-public:
       gcloud builds triggers run web-public-deploy

    6. Grant Cloud Run invoker access (Google Cloud Console):
       Cloud Run > web-admin > Security > Add Principal
       Grant role: Cloud Run Invoker (roles/run.invoker)

    7. Access web-admin via authenticated proxy:
       gcloud run services proxy web-admin --region ${var.region}
       # Then open http://localhost:8080 in your browser

  EOT
}
