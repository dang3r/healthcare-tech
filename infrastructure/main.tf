provider "google" {
  project = "health-tech-340502"
  region  = "us-central1"
  zone    = "us-central1-c"
}

resource "google_storage_bucket" "fda_devices" {
  name          = "fda_devices"
  location      = "US"
  force_destroy = true

  uniform_bucket_level_access = true
}

resource "google_service_account" "github" {
  account_id   = "github"
  display_name = "A service account for uploading files from Github Actions to GCS"
}

resource "google_project_iam_binding" "gcs_read" {
  project = "health-tech-340502"
  role    = "roles/storage.objectViewer"
  members = ["serviceAccount:${google_service_account.github.email}"]

  condition {
    title       = "Listing files from GCS"
    description = "Only listing files from a specific bucket"
    expression  = "resource.name.startsWith('projects/health-tech-340502/buckets/fda_devices')"
  }
}

resource "google_project_iam_binding" "gcs_write" {
  project = "health-tech-340502"
  role    = "roles/storage.objectCreator"
  members = ["serviceAccount:${google_service_account.github.email}"]

  condition {
    title       = "Upload files to GCS"
    description = "Only upload files to specific bucket"
    expression  = "resource.name.startsWith('projects/health-tech-340502/fda_devices/raw')"
  }
}
