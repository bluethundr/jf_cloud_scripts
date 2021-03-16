// Configure the Google Cloud provider
provider "google" {
  credentials = file("jokefiregcp-b9ee29dfd7cd.json")
  project     = "jokefiregcp"
  region      = var.region
}

// Terraform plugin for creating random ids
resource "random_id" "instance_id" {
  byte_length = 8
}

// A single Compute Engine instance
resource "google_compute_instance" "default" {
  name         = var.instance_name
  machine_type = var.machine_type
  zone         = var.zone

  tags = [var.instance_name, var.env_name]
  boot_disk {
    initialize_params {
      image = "debian-cloud/debian-9"
    }

  }

  // Make sure flask is installed on all new instances for later steps
  metadata_startup_script = "sudo apt-get update; sudo apt-get install -yq build-essential python-pip rsync; pip install flask"

  metadata = {
    ssh-keys = "bluet:${file("id_rsa.pub")}"
  }

  network_interface {
    network = "default"
  }
}

resource "google_compute_snapshot" "snapshot" {
  name        = var.instance_name
  source_disk = google_compute_disk.persistent.name
  zone        = var.zone
  labels = {
    my_label = "value"
  }
  storage_locations = ["us-central1"]
}

data "google_compute_image" "debian" {
  family  = "debian-9"
  project = "debian-cloud"
}

resource "google_compute_disk" "persistent" {
  name  = "debian-disk"
  image = data.google_compute_image.debian.self_link
  size  = 10
  type  = "pd-ssd"
  zone  = var.zone
}