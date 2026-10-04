output "telemetry_lake_bucket" {
  description = "S3 Data Lake bucket name"
  value       = aws_s3_bucket.telemetry_lake.bucket
}

output "model_artifacts_bucket" {
  description = "S3 Model Registry bucket name"
  value       = aws_s3_bucket.model_artifacts.bucket
}

output "kms_key_arn" {
  description = "KMS Encryption Key ARN"
  value       = aws_kms_key.ge_pdm_kms.arn
}

output "kafka_bootstrap_brokers_tls" {
  description = "MSK TLS Bootstrap Brokers"
  value       = aws_msk_cluster.kafka_telemetry.bootstrap_brokers_tls
}
