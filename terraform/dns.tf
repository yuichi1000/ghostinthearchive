# Cloud DNS configuration for ghostinthearchive.ai

# DNS Zone
resource "google_dns_managed_zone" "main" {
  name        = "ghostinthearchive-zone"
  dns_name    = "${var.domain}."
  description = "DNS zone for Ghost in the Archive"

  depends_on = [google_project_service.apis]
}

# admin subdomain → HTTPS LB static IP (IAP-protected)
resource "google_dns_record_set" "admin" {
  name         = "${var.admin_subdomain}.${var.domain}."
  managed_zone = google_dns_managed_zone.main.name
  type         = "A"
  ttl          = 300
  rrdatas      = [google_compute_global_address.web_admin.address]
}

# Output nameservers for Spaceship configuration
output "nameservers" {
  description = "Nameservers to configure in Spaceship"
  value       = google_dns_managed_zone.main.name_servers
}
