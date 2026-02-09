# Cloud IAP + HTTPS Load Balancer for web-admin
# Provides authenticated access to admin.ghostinthearchive.ai

# Project data for project number
data "google_project" "current" {}

# Static IP for the load balancer
resource "google_compute_global_address" "web_admin" {
  name = "web-admin-ip"

  depends_on = [google_project_service.apis]
}

# Serverless NEG to connect Cloud Run to the load balancer
resource "google_compute_region_network_endpoint_group" "web_admin" {
  name                  = "web-admin-neg"
  network_endpoint_type = "SERVERLESS"
  region                = var.region

  cloud_run {
    service = google_cloud_run_v2_service.web_admin.name
  }

  depends_on = [google_project_service.apis]
}

# Backend service with IAP enabled
resource "google_compute_backend_service" "web_admin" {
  name                  = "web-admin-backend"
  protocol              = "HTTPS"
  load_balancing_scheme = "EXTERNAL_MANAGED"

  backend {
    group = google_compute_region_network_endpoint_group.web_admin.id
  }

  iap {
    oauth2_client_id     = " "
    oauth2_client_secret = " "
  }

  depends_on = [google_project_service.apis]
}

# URL map
resource "google_compute_url_map" "web_admin" {
  name            = "web-admin-url-map"
  default_service = google_compute_backend_service.web_admin.id
}

# Managed SSL certificate
resource "google_compute_managed_ssl_certificate" "web_admin" {
  name = "web-admin-cert"

  managed {
    domains = ["${var.admin_subdomain}.${var.domain}"]
  }

  depends_on = [google_project_service.apis]
}

# HTTPS proxy
resource "google_compute_target_https_proxy" "web_admin" {
  name             = "web-admin-https-proxy"
  url_map          = google_compute_url_map.web_admin.id
  ssl_certificates = [google_compute_managed_ssl_certificate.web_admin.id]
}

# HTTPS forwarding rule
resource "google_compute_global_forwarding_rule" "web_admin_https" {
  name                  = "web-admin-https-rule"
  target                = google_compute_target_https_proxy.web_admin.id
  port_range            = "443"
  ip_address            = google_compute_global_address.web_admin.id
  load_balancing_scheme = "EXTERNAL_MANAGED"

  depends_on = [google_project_service.apis]
}

# HTTP → HTTPS redirect
resource "google_compute_url_map" "web_admin_redirect" {
  name = "web-admin-http-redirect"

  default_url_redirect {
    https_redirect         = true
    strip_query            = false
    redirect_response_code = "MOVED_PERMANENTLY_DEFAULT"
  }
}

resource "google_compute_target_http_proxy" "web_admin_redirect" {
  name    = "web-admin-http-proxy"
  url_map = google_compute_url_map.web_admin_redirect.id
}

resource "google_compute_global_forwarding_rule" "web_admin_http" {
  name                  = "web-admin-http-rule"
  target                = google_compute_target_http_proxy.web_admin_redirect.id
  port_range            = "80"
  ip_address            = google_compute_global_address.web_admin.id
  load_balancing_scheme = "EXTERNAL_MANAGED"

  depends_on = [google_project_service.apis]
}

# Grant IAP service agent permission to invoke Cloud Run
resource "google_cloud_run_v2_service_iam_member" "iap_invoker" {
  name     = google_cloud_run_v2_service.web_admin.name
  location = var.region
  role     = "roles/run.invoker"
  member   = "serviceAccount:service-${data.google_project.current.number}@gcp-sa-iap.iam.gserviceaccount.com"
}
