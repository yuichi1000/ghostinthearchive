# Secret Manager configuration

# NextAuth secret
resource "google_secret_manager_secret" "nextauth_secret" {
  secret_id = "nextauth-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Google OAuth client ID
resource "google_secret_manager_secret" "google_oauth_client_id" {
  secret_id = "google-oauth-client-id"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Google OAuth client secret
resource "google_secret_manager_secret" "google_oauth_client_secret" {
  secret_id = "google-oauth-client-secret"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# DPLA API key
resource "google_secret_manager_secret" "dpla_api_key" {
  secret_id = "dpla-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# NYPL API token
resource "google_secret_manager_secret" "nypl_api_token" {
  secret_id = "nypl-api-token"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# OpenRouter API key (Storyteller LLM selection via OpenRouter)
resource "google_secret_manager_secret" "openrouter_api_key" {
  secret_id = "openrouter-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Europeana API key (European cultural heritage archive search)
resource "google_secret_manager_secret" "europeana_api_key" {
  secret_id = "europeana-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# OpenAlex API key (academic paper search)
resource "google_secret_manager_secret" "openalex_api_key" {
  secret_id = "openalex-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# DDB API key (Deutsche Digitale Bibliothek OAuth)
resource "google_secret_manager_secret" "ddb_api_key" {
  secret_id = "ddb-api-key"

  replication {
    auto {}
  }

  depends_on = [google_project_service.apis]
}

# Output instructions for setting secret values
output "secret_setup_instructions" {
  description = "Instructions for setting up secrets"
  value       = <<-EOT
    Set secret values using the following commands:

    echo -n "YOUR_VALUE" | gcloud secrets versions add nextauth-secret --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add google-oauth-client-id --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add google-oauth-client-secret --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add dpla-api-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add nypl-api-token --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add openrouter-api-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add europeana-api-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add openalex-api-key --data-file=-
    echo -n "YOUR_VALUE" | gcloud secrets versions add ddb-api-key --data-file=-
  EOT
}
