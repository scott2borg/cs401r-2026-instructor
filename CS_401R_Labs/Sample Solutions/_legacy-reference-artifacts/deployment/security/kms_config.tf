# ────────────────────────────────────────────────────────────────────────────────
# NorthStar Retail AI Platform — KMS Encryption Key Configuration
# Lab 5: Production Security
# ────────────────────────────────────────────────────────────────────────────────
#
# Why KMS here (not SSE-S3)?
# Lab 1 used SSE-S3 (AES-256, AWS-managed keys) — simple and free.
# Lab 5 upgrades to SSE-KMS (customer-managed keys, CMK) for three reasons:
#   1. Audit trail: Every Encrypt/Decrypt call is logged in CloudTrail.
#      With SSE-S3, there is no per-object key usage log.
#   2. Access control: KMS key policy controls which IAM roles can decrypt.
#      SSE-S3 cannot restrict decryption — any IAM user with S3 GetObject can read.
#   3. Key rotation: CMKs rotate annually by default; SSE-S3 rotation is opaque.
#
# This key encrypts:
#   - S3 bucket objects (raw customer data, feature store exports, inference outputs)
#   - SageMaker Feature Store offline store
#   - SageMaker training job storage volume (via SageMaker resource config)
#   - Batch Transform output files
#
# Key policy design:
#   - Root account: Full kms:* (break-glass / key administration)
#   - ML/Data Engineer roles: GenerateDataKey + Decrypt only (use the key, not manage it)
#   - Model Monitor role: GenerateDataKey + Decrypt (reads predictions for drift analysis)
#   - No cross-account grants in this policy — add a separate Grant for cross-account
#     access if NorthStar adds a data warehouse account.
# ────────────────────────────────────────────────────────────────────────────────

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

# ─── Variables ────────────────────────────────────────────────────────────────

variable "aws_account_id" {
  type        = string
  description = "AWS account ID. Used to construct IAM ARNs in the key policy."
}

variable "project_name" {
  type        = string
  default     = "NorthStar"
  description = "Project prefix used in IAM role names (e.g., NorthStar-MLEngineer)."
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Common tags applied to all KMS resources."
}

variable "deletion_window_days" {
  type        = number
  default     = 30
  description = "Number of days before a scheduled key deletion takes effect (7–30)."
}

# ─── KMS Key ─────────────────────────────────────────────────────────────────

resource "aws_kms_key" "northstar_data" {
  description             = "NorthStar Retail AI Platform — data encryption key"
  deletion_window_in_days = var.deletion_window_days

  # Automatic annual key rotation. AWS creates a new cryptographic backing key each year.
  # Existing ciphertext decrypts correctly — AWS tracks which backing key encrypted which object.
  # Rotation does NOT change the key ARN or alias — all references remain valid.
  enable_key_rotation = true

  # Multi-region: false. NorthStar operates in a single region (us-east-1).
  # Enable multi-region only if you add a disaster recovery region.
  multi_region = false

  tags = merge(var.tags, {
    Name        = "${var.project_name}-data-encryption"
    ManagedBy   = "Terraform"
    SecurityTier = "Restricted"
  })
}

# ─── KMS Alias ────────────────────────────────────────────────────────────────
# Human-readable alias used in S3 bucket policies and SageMaker configs.
# Using an alias (not the key ARN) allows the underlying key to be rotated
# without updating every resource that references it.

resource "aws_kms_alias" "northstar_data" {
  name          = "alias/northstar-data-encryption"
  target_key_id = aws_kms_key.northstar_data.key_id
}

# ─── Key Policy ───────────────────────────────────────────────────────────────
# Principle of least privilege:
#   - Root: full kms:* (required; without this, key cannot be managed if all
#     other access is accidentally removed — AWS best practice)
#   - ML/Data Engineer roles: use-only permissions (generate data keys + decrypt)
#   - Model Monitor role: same use-only permissions
#   - No kms:DeleteAlias, kms:ScheduleKeyDeletion, kms:PutKeyPolicy granted to workload roles

resource "aws_kms_key_policy" "northstar_data" {
  key_id = aws_kms_key.northstar_data.id

  policy = jsonencode({
    Version = "2012-10-17"
    Id      = "northstar-data-key-policy"
    Statement = [
      # Statement 1: Root account full access (key administration)
      # Required by AWS — if all other grants are removed, root can recover.
      {
        Sid    = "AllowKeyAdministration"
        Effect = "Allow"
        Principal = {
          AWS = "arn:aws:iam::${var.aws_account_id}:root"
        }
        Action   = "kms:*"
        Resource = "*"
      },

      # Statement 2: ML workload roles — use the key for data operations.
      # GenerateDataKey: needed to write encrypted objects to S3.
      # Decrypt: needed to read encrypted objects from S3.
      # DescribeKey: needed to verify the key ARN in CLI commands and SDK calls.
      # ReEncryptFrom/To: needed if SageMaker copies encrypted artifacts between jobs.
      {
        Sid    = "AllowMLWorkloads"
        Effect = "Allow"
        Principal = {
          AWS = [
            "arn:aws:iam::${var.aws_account_id}:role/${var.project_name}-MLEngineer",
            "arn:aws:iam::${var.aws_account_id}:role/${var.project_name}-DataEngineer",
            "arn:aws:iam::${var.aws_account_id}:role/${var.project_name}-ModelMonitor",
          ]
        }
        Action = [
          "kms:GenerateDataKey",
          "kms:GenerateDataKeyWithoutPlaintext",
          "kms:Decrypt",
          "kms:DescribeKey",
          "kms:ReEncryptFrom",
          "kms:ReEncryptTo",
        ]
        Resource = "*"
        # Condition: Only allow key usage from within the NorthStar VPC endpoint.
        # This prevents decryption even if credentials are stolen and used externally.
        Condition = {
          StringEquals = {
            "aws:SourceVpce" = "vpce-${var.aws_account_id}"
          }
        }
      },

      # Statement 3: SageMaker service principal — needed for Feature Store,
      # training job encryption, and Batch Transform output encryption.
      # SageMaker uses the key on behalf of the execution role, so the service
      # principal must be explicitly granted.
      {
        Sid    = "AllowSageMakerService"
        Effect = "Allow"
        Principal = {
          Service = "sagemaker.amazonaws.com"
        }
        Action = [
          "kms:GenerateDataKey",
          "kms:Decrypt",
          "kms:DescribeKey",
        ]
        Resource = "*"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = var.aws_account_id
          }
        }
      },
    ]
  })
}

# ─── Outputs ─────────────────────────────────────────────────────────────────

output "kms_key_arn" {
  value       = aws_kms_key.northstar_data.arn
  description = "KMS key ARN — use in S3 bucket SSE-KMS configuration and SageMaker resource configs."
}

output "kms_key_id" {
  value       = aws_kms_key.northstar_data.key_id
  description = "KMS key ID — use when referencing the key in CLI commands."
}

output "kms_alias_arn" {
  value       = aws_kms_alias.northstar_data.arn
  description = "KMS alias ARN — preferred reference in resource policies (stable across key rotation)."
}
