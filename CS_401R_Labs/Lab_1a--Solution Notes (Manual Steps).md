
## Lab 1a — Console Execution (Manual Steps)

**Order matters:** Start Task A4 (SageMaker Domain) early — it takes 8–12 minutes to provision. The order below is optimized for wall time.

---

### Task A1 — Draw the Diagram First

Before touching the console, draw the diagram using [Cloudcraft](https://cloudcraft.co/) or [draw.io](https://app.diagrams.net/). Use the Connection Map in the lab guide. Save as:

- `docs/lab1-architecture-diagram.png`
- `docs/lab1-architecture-diagram-source.xml` (or `.drawio`)

---

### Task A2 — Network Layer

**Step 1: Create VPC**

- Console → VPC → Your VPCs → **Create VPC**
- Resources to create: `VPC only`
- Name: `northstar-dev-vpc`
- IPv4 CIDR: `10.0.0.0/16`
- Tenancy: Default
- DNS hostnames: ✅ Enable
- DNS resolution: ✅ Enable
- → **Create VPC**

```bash
# Verify
aws ec2 describe-vpcs --filters "Name=tag:Name,Values=northstar-dev-vpc" \
  --query 'Vpcs[*].{Id:VpcId,CIDR:CidrBlock,DNS:EnableDnsHostnames}'
```

bash

**Step 2: Create Public Subnet**

- VPC → Subnets → **Create subnet**
- VPC: `northstar-dev-vpc`
- Subnet name: `northstar-dev-public-1`
- AZ: `us-east-1a`
- IPv4 CIDR: `10.0.100.0/24`
- → **Create subnet**
- Select subnet → Actions → **Edit subnet settings** → ✅ Enable auto-assign public IPv4 address → Save

```bash
# Verify
aws ec2 describe-subnets --filters "Name=tag:Name,Values=northstar-dev-public-1" \
  --query 'Subnets[*].{Id:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock,AutoPublicIP:MapPublicIpOnLaunch}'
```

bash

**Step 3: Create and Attach Internet Gateway**

- VPC → Internet Gateways → **Create internet gateway**
- Name: `northstar-dev-igw`
- → **Create**
- Select `northstar-dev-igw` → Actions → **Attach to VPC** → select `northstar-dev-vpc` → Attach

```bash
# Verify
aws ec2 describe-internet-gateways --filters "Name=tag:Name,Values=northstar-dev-igw" \
  --query 'InternetGateways[*].{Id:InternetGatewayId,State:Attachments[0].State,VPC:Attachments[0].VpcId}'
```

bash

**Step 4: Update Route Table**

- VPC → Route Tables → find the route table automatically created with `northstar-dev-vpc` (it will show 1 subnet association or none — not the Main route table for the default VPC)
- Select it → **Edit routes** → **Add route**
    - Destination: `0.0.0.0/0`
    - Target: Internet Gateway → `northstar-dev-igw`
    - → **Save changes**
- **Subnet associations** tab → **Edit subnet associations** → select `northstar-dev-public-1` → **Save**
- Name the route table: `northstar-dev-public-rt`

```bash
# Verify (get VPC ID first from step 1 output, then):
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=tag:Name,Values=northstar-dev-vpc" \
  --query 'Vpcs[0].VpcId' --output text)
aws ec2 describe-route-tables --filters "Name=vpc-id,Values=${VPC_ID}" \
  --query 'RouteTables[*].{Routes:Routes,Associations:Associations[*].SubnetId}'
```

bash

**Step 5: Create Security Group**

- VPC → Security Groups → **Create security group**
- Name: `northstar-dev-sagemaker-sg`
- Description: `SageMaker Studio — intra-VPC inbound only`
- VPC: `northstar-dev-vpc`
- Inbound rules → Add rule:
    - Type: `All traffic` | Source: `Custom` → `10.0.0.0/16`
- Outbound rules: leave default (All traffic `0.0.0.0/0`)
- → **Create security group**

```bash
# Verify
aws ec2 describe-security-groups --filters "Name=tag:Name,Values=northstar-dev-sagemaker-sg" \
  --query 'SecurityGroups[*].{Id:GroupId,Inbound:IpPermissions,Outbound:IpPermissionsEgress}'
```

bash

---

### Task A3 — Storage and IAM

**Step 6: Create S3 Bucket**

First get your account ID:

```bash
aws sts get-caller-identity --query Account --output text
```

bash

- S3 → **Create bucket**
- Bucket name: `northstar-dev-data-YOUR_ACCOUNT_ID` (replace with real 12-digit ID)
- Region: `us-east-1`
- Block all public access: ✅ all four boxes
- Bucket versioning: **Enable**
- Default encryption: SSE-S3 (AES-256)
- → **Create bucket**

**Create 4 folder prefixes** — select bucket → **Create folder** (repeat 4×):

- `raw/`
- `processed/`
- `features/`
- `artifacts/`

```bash
# Verify
BUCKET="northstar-dev-data-$(aws sts get-caller-identity --query Account --output text)"
aws s3api get-bucket-versioning --bucket "${BUCKET}"
aws s3api get-bucket-encryption --bucket "${BUCKET}"
aws s3 ls s3://${BUCKET}/
```

bash

**Step 7: Create IAM Role**

- IAM → Roles → **Create role**
- Trusted entity: AWS service → **SageMaker**
- Use case: `SageMaker` (not Studio)
- → **Next** (skip adding managed policies)
- Role name: `northstar-dev-MLEngineer`
- → **Create role**

Then add the inline policy:

- Open `northstar-dev-MLEngineer` → **Add permissions** → **Create inline policy**
- Switch to **JSON** editor, paste the policy from the lab guide (Task A3 section)
- Policy name: `NorthStarMLEngineerPolicy`
- → **Create policy**

```bash
# Verify
aws iam get-role --role-name northstar-dev-MLEngineer \
  --query 'Role.{ARN:Arn,Trust:AssumeRolePolicyDocument}'
aws iam list-role-policies --role-name northstar-dev-MLEngineer
```

bash

---

### Task A4 — SageMaker Domain _(Start this before A3 if possible)_

**Step 8: Create SageMaker Domain**

- SageMaker → Domains → **Create domain** → **Standard setup**
- Domain name: `northstar-dev-domain`
- Auth mode: `IAM`
- Default execution role: `northstar-dev-MLEngineer`

Network section:

- VPC: `northstar-dev-vpc`
- Subnet: `northstar-dev-public-1`
- Security group: `northstar-dev-sagemaker-sg`

App settings:

- Notebook output sharing: `Disabled`
- Default instance type: `ml.t3.medium`
- → **Submit** — wait **8–12 minutes** for status: **InService**

```bash
# Poll status (run every 60s while waiting)
aws sagemaker list-domains \
  --query 'Domains[?DomainName==`northstar-dev-domain`].{Id:DomainId,Status:Status}'
```

bash

**Step 9: Create User Profile and Launch Studio**

- Select `northstar-dev-domain` → **Add user** (or Launch Studio if profile exists)
- User profile name: `MLEngineer`
- Execution role: `northstar-dev-MLEngineer`
- → **Submit** → **Launch Studio**
- Verify JupyterLab opens

**Step 10: Shut Down (Required — costs money if left running)**

- In Studio: **File → Shut Down → Shut Down All**
- Wait for Running Instances panel to show 0 active apps
- Screenshot this panel → save as `docs/lab1a-studio-shutdown.png`

```bash
# Verify domain is InService
DOMAIN_ID=$(aws sagemaker list-domains \
  --query 'Domains[?DomainName==`northstar-dev-domain`].DomainId' --output text)
aws sagemaker describe-domain --domain-id "${DOMAIN_ID}" \
  --query '{Status:Status,VPC:VpcId,Subnet:SubnetIds[0]}'
```