terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 2.70"
    }
  }
}

provider "aws" {
  profile = "jf-master-pd-gov"
  region  = var.region["jf-master-pd-gov"]
}

resource "aws_instance" "jf-aws" {
  ami                    = var.amis["us-gov-west-1"]
  instance_type          = "t2.micro"
  vpc_security_group_ids = var.vpc_security_group_ids["jf-master-pd-gov"]
  subnet_id              = var.subnet_id["jf-master-pd-gov"]
  key_name               = "jf-timd-keypair"
  tags = {
    Name = "jf-web1"
  }
}

resource "aws_key_pair" "jf-timd-keypair" {
  key_name   = "jf-timd-keypair"
  public_key = file("C:\\Users\\bluet\\.ssh\\id_rsa.pub")
}

