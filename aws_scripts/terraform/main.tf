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
  region  = var.region
}

resource "aws_instance" "example" {
  ami                    = var.amis["us-gov-west-1"]
  instance_type          = "t2.micro"
  vpc_security_group_ids = ["sg-7f051404"]
  subnet_id              = "subnet-4dad6304"
  key_name               = "jf-timd-gov-keypair"
}

resource "aws_key_pair" "jf-timd-gov-keypair" {
  key_name   = "jf-timd-gov-keypair"
  public_key = "ssh-rsa AAAAB3NzaC1yc2EAAAABIwAAAQEAvh1RdiRPJBeJzln/uoxbFQAUJXnbBXzmmw1VZMs4WVSH8FaKsFt3eoakhid5nCdY7EwdT7PE0H6ACyELu2GMYHZ3pJXrbyNG196XK4QUT8Cj7/iG6Onwj3esjT90BaBuSB/q1s9D6NzVumJc1WDKVUkF6JSe1mSK9tECgCc9Vu9YOg69/mZ63VJsTKlaLrjndtRowT1F8dWeNCU3pQGHxdfdesFwopWydEmfwuj0yzXw5HebJZWb0ju8ajdeW6bsyvYHnr5Vi0hJ9Hily74u7H6BSU25jjKOWND/v6jDY/nyyBdPvEsN3PEeiIrejnVWIeqKvhzmBWE7bdcFspIJvw== dunphy@BAM-025715-TD.local tdunphy@gmail.com"
}

