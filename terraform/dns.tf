# Cloud DNS configuration for ghostinthearchive.ai

# DNS Zone
resource "google_dns_managed_zone" "main" {
  name        = "ghostinthearchive-zone"
  dns_name    = "${var.domain}."
  description = "DNS zone for Ghost in the Archive"

  depends_on = [google_project_service.apis]
}

# A record for admin subdomain -> Cloud Run
resource "google_dns_record_set" "admin" {
  name         = "${var.admin_subdomain}.${var.domain}."
  type         = "CNAME"
  ttl          = 300
  managed_zone = google_dns_managed_zone.main.name
  rrdatas      = ["ghs.googlehosted.com."]
}

# Output nameservers for GoDaddy configuration
output "nameservers" {
  description = "Nameservers to configure in GoDaddy"
  value       = google_dns_managed_zone.main.name_servers
}
