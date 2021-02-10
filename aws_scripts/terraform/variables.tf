variable "region" {
  type = map(string)
  default = {
    "jf-master-pd"     = "us-east-1"
    "jf-master-pd-gov" = "us-gov-west-1"
  }
}

variable "amis" {
  type = map(string)
  default = {
    "us-east-1-ubuntu"      = "ami-0885b1f6bd170450c"
    "us-east-1-centos8"     = "ami-05954d92f270b425a"
    "us-west-2-ubuntu"      = "ami-07dd19a7900a1f049"
    "us-west-2-centos8"     = "ami-053c57d20f2a08858"
    "us-gov-west-1-ubuntu"  = "ami-84556de5"
    "us-gov-west-1-centos8" = "ami-27b29a46"
    "us-gov-east-1-ubuntu"  = "ami-dee008af"
    "us-gov-east-1-centos8" = "ami-016bec6924268abc8"
  }
}

variable "vpc_security_group_ids" {
  type = map(list(string))
  default = {
    "jf-master-pd"     = ["sg-0333d9eaaeb3ab1b0"]
    "jf-master-pd-gov" = ["sg-7f051404"]
  }
}


variable "subnet_id" {
  type = map(string)
  default = {
    "jf-master-pd"     = "subnet-3ab1835d"
    "jf-master-pd-gov" = "subnet-4dad6304"
  }
}