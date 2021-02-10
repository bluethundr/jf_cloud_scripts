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
    "us-east-1"     = "ami-0885b1f6bd170450c"
    "us-west-2"     = "ami-07dd19a7900a1f049"
    "us-gov-west-1" = "ami-84556de5"
    "us-gov-east-1" = "ami-dee008af"
  }
}

variable "vpc_security_group_ids" {
  type = map(string)
  default = {
    "jf-master-pd"     = "sg-0333d9eaaeb3ab1b0"
    "jf-master-pd-gov" = "sg-7f051404"
  }
}


variable "subnet_id" {
  type = map(string)
  default = {
    "jf-master-pd"     = "subnet-3ab1835d"
    "jf-master-pd-gov" = "subnet-4dad6304"
  }
}