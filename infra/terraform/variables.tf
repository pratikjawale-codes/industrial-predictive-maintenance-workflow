variable "aws_region" {
  description = "Target AWS region"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "prod"
}

variable "vpc_id" {
  description = "Target VPC ID"
  type        = string
  default     = "vpc-0a1b2c3d4e5f67890"
}

variable "subnet_ids" {
  description = "VPC subnets across availability zones"
  type        = list(string)
  default     = ["subnet-11111111", "subnet-22222222", "subnet-33333333"]
}

variable "plant_edge_gateway_cidrs" {
  description = "Allowed CIDR blocks from GE plant edge gateways"
  type        = list(string)
  default     = ["10.100.0.0/16", "10.101.0.0/16", "10.102.0.0/16"]
}
