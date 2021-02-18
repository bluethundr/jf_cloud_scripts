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
  region  = var.region["jf-master-pd"]
}

resource "aws_instance" "jf-aws-instance" {
  ami = var.amis["us-east-1"]
  #ami                    = var.amis[var.region]
  instance_type          = "t3.micro"
  vpc_security_group_ids = var.vpc_security_group_ids["jf-master-pd"]
  subnet_id              = var.subnet_id["jf-master-pd"]
  key_name               = "jf-timd-keypair"
  tags = {
    Name = "jf-web1"
  }
}

resource "aws_key_pair" "jf-timd-keypair" {
  key_name   = "jf-timd-keypair"
  public_key = file("C:\\Users\\bluet\\.ssh\\id_rsa.pub")
}

