terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 2.70"
    }
  }
}

provider "aws" {
  profile = "jf-master-pd"
  region  = var.region
}

resource "aws_instance" "example" {
  ami                    = var.amis["us-east-1"]
  instance_type          = "t2.micro"
  vpc_security_group_ids = ["sg-0333d9eaaeb3ab1b0"]
  subnet_id              = "subnet-3ab1835d"
  key_name               = "jf-timd-keypair"
}

resource "aws_key_pair" "jf-timd-keypair" {
  key_name   = "jf-timd-keypair"
  public_key = file("C:\\Users\\bluet\\.ssh\\id_rsa.pub")
}

