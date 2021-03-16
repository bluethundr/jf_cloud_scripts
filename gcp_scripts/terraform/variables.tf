variable "instance_name" {
  description = "Value of the Name tag for the GCP instance"
  type        = string
  default     = "dev-sql-1aaa-e1d"
}

variable "env_name" {
  description = "Value of the Environment tag for the GCP instance"
  type        = string
  default     = "dev"
}

variable "region" {
  description = "Value of the Region for the GCP instance"
  type        = string
  default     = "us-west1"
}

variable "zone" {
  description = "Value of the Zone for the GCP instance"
  type        = string
  default     = "us-west1-a"
}


variable "machine_type" {
  description = "Value of the Machine Type for the GCP instance"
  type        = string
  default     = "f1-micro"
}

