# Terraform configuration for GE AI Predictive Maintenance Platform (Section 6 & 14)
terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# 1. KMS Customer Managed Key for Enterprise Encryption at Rest
resource "aws_kms_key" "ge_pdm_kms" {
  description             = "KMS Key for GE Predictive Maintenance Telemetry & Models"
  deletion_window_in_days = 30
  enable_key_rotation     = true
  tags = {
    Environment = var.environment
    Client      = "General Electric"
    Project     = "AI Predictive Maintenance"
  }
}

# 2. Immutable Raw Telemetry S3 Data Lake
resource "aws_s3_bucket" "telemetry_lake" {
  bucket = "ge-telemetry-lake-${var.environment}"
  tags = {
    DataClassification = "Industrial-IoT-Restricted"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "telemetry_lake_enc" {
  bucket = aws_s3_bucket.telemetry_lake.id
  rule {
    apply_server_side_encryption_by_default {
      kms_master_key_id = aws_kms_key.ge_pdm_kms.arn
      sse_algorithm     = "aws:kms"
    }
  }
}

resource "aws_s3_bucket_lifecycle_configuration" "lake_lifecycle" {
  bucket = aws_s3_bucket.telemetry_lake.id
  rule {
    id     = "telemetry-hot-warm-cold"
    status = "Enabled"
    transition {
      days          = 90
      storage_class = "STANDARD_IA"
    }
    transition {
      days          = 365
      storage_class = "GLACIER"
    }
  }
}

# 3. Model Artifacts & Registry Bucket
resource "aws_s3_bucket" "model_artifacts" {
  bucket = "ge-pdm-model-artifacts-${var.environment}"
}

# 4. Amazon MSK (Managed Streaming for Apache Kafka)
resource "aws_msk_cluster" "kafka_telemetry" {
  cluster_name           = "ge-telemetry-cluster-${var.environment}"
  kafka_version          = "3.5.1"
  number_of_broker_nodes = 3

  broker_node_group_info {
    instance_type   = "kafka.m5.large"
    client_subnets  = var.subnet_ids
    security_groups = [aws_security_group.kafka_sg.id]
  }

  encryption_info {
    encryption_in_transit {
      client_broker = "TLS"
      in_cluster    = true
    }
    encryption_at_rest_kms_key_arn = aws_kms_key.ge_pdm_kms.arn
  }
}

# 5. Security Group for Kafka Ingestion
resource "aws_security_group" "kafka_sg" {
  name        = "ge-kafka-sg-${var.environment}"
  description = "Controls telemetry stream access to Kafka"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 9094
    to_port     = 9094
    protocol    = "tcp"
    cidr_blocks = var.plant_edge_gateway_cidrs
    description = "TLS ingestion from plant edge gateways"
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
