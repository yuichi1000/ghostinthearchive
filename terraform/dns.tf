# Cloud DNS configuration for ghostinthearchive.ai

# DNS Zone
resource "google_dns_managed_zone" "main" {
  name        = "ghostinthearchive-zone"
  dns_name    = "${var.domain}."
  description = "DNS zone for Ghost in the Archive"

  depends_on = [google_project_service.apis]
}

# admin subdomain DNS record removed — web-admin is accessed via
# gcloud run services proxy (Cloud Run IAM authentication)

# Output nameservers for Spaceship configuration
output "nameservers" {
  description = "Nameservers to configure in Spaceship"
  value       = google_dns_managed_zone.main.name_servers
}
