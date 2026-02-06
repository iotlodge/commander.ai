# AWS Cloud Deployment Guide

> Deploy commander.ai to AWS using AWS CDK (Cloud Development Kit) for production-ready infrastructure

[![AWS](https://img.shields.io/badge/AWS-Cloud%20Ready-orange.svg)](https://aws.amazon.com/)
[![CDK](https://img.shields.io/badge/AWS%20CDK-TypeScript-blue.svg)](https://aws.amazon.com/cdk/)

---

## 🏗️ AWS Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CloudFront CDN                            │
│                     (Global Distribution)                        │
└────────────┬──────────────────────────────────┬─────────────────┘
             │                                   │
    ┌────────▼────────┐                ┌────────▼─────────┐
    │   S3 Bucket     │                │   API Gateway    │
    │  (Frontend)     │                │  (WebSocket)     │
    └─────────────────┘                └────────┬─────────┘
                                                 │
                                        ┌────────▼─────────┐
                                        │  Application     │
                                        │  Load Balancer   │
                                        └────────┬─────────┘
                                                 │
                    ┌────────────────────────────┼────────────────────────┐
                    │                            │                        │
           ┌────────▼─────────┐        ┌────────▼─────────┐    ┌────────▼─────────┐
           │   ECS Fargate    │        │   ECS Fargate    │    │   ECS Fargate    │
           │  Backend API 1   │        │  Backend API 2   │    │   Qdrant Vector  │
           │  (FastAPI)       │        │  (FastAPI)       │    │   Database       │
           └──────────────────┘        └──────────────────┘    └──────────────────┘
                    │                            │
                    └────────────┬───────────────┘
                                 │
                    ┌────────────▼───────────────┐
                    │        VPC Private         │
                    │         Subnets            │
                    └────────────┬───────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐    ┌─────────▼─────────┐    ┌────────▼────────┐
│  RDS PostgreSQL│    │  ElastiCache      │    │   Secrets       │
│  (pgvector)    │    │  Redis            │    │   Manager       │
│  Multi-AZ      │    │  Cluster Mode     │    │                 │
└────────────────┘    └───────────────────┘    └─────────────────┘
```

---

## 🎯 AWS Services Used

### Compute & Containers
- **ECS Fargate** - Serverless containers for backend API and Qdrant
- **Application Load Balancer** - Distribute traffic across backend instances
- **API Gateway** - WebSocket connections for real-time updates

### Storage & Databases
- **RDS PostgreSQL 16** - Managed database with pgvector extension
- **ElastiCache Redis** - In-memory cache (cluster mode enabled)
- **S3** - Static frontend hosting and file storage

### Networking & Security
- **VPC** - Isolated network with public/private subnets
- **Security Groups** - Firewall rules for each service
- **Secrets Manager** - Secure API key storage
- **CloudFront** - CDN for global distribution
- **Route 53** - DNS management
- **ACM** - SSL/TLS certificates

### Monitoring & Operations
- **CloudWatch** - Logs, metrics, alarms
- **X-Ray** - Distributed tracing
- **CloudTrail** - Audit logging
- **SNS** - Alert notifications

---

## 🚀 Quick Start

### Prerequisites

```bash
# Install AWS CDK
npm install -g aws-cdk

# Install AWS CLI
brew install awscli  # macOS
# or: pip install awscli

# Configure AWS credentials
aws configure
```

### Project Setup

```bash
# Navigate to infrastructure directory
mkdir -p infrastructure/cdk
cd infrastructure/cdk

# Initialize CDK project
cdk init app --language=typescript

# Install dependencies
npm install
```

---

## 📦 CDK Stack Structure

### Directory Layout

```
infrastructure/
├── cdk/
│   ├── bin/
│   │   └── commander-ai.ts           # CDK app entry point
│   ├── lib/
│   │   ├── network-stack.ts          # VPC, subnets, security groups
│   │   ├── database-stack.ts         # RDS PostgreSQL
│   │   ├── cache-stack.ts            # ElastiCache Redis
│   │   ├── qdrant-stack.ts           # Qdrant vector DB on ECS
│   │   ├── backend-stack.ts          # FastAPI on ECS
│   │   ├── frontend-stack.ts         # S3 + CloudFront
│   │   ├── websocket-stack.ts        # API Gateway WebSocket
│   │   └── monitoring-stack.ts       # CloudWatch, alarms
│   ├── config/
│   │   ├── dev.ts                    # Dev environment config
│   │   ├── staging.ts                # Staging config
│   │   └── prod.ts                   # Production config
│   ├── cdk.json
│   ├── package.json
│   └── tsconfig.json
└── docker/
    ├── backend.Dockerfile            # FastAPI production image
    └── qdrant.Dockerfile             # Qdrant custom image
```

---

## 🔧 CDK Implementation

### 1. Network Stack

```typescript
// lib/network-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export class NetworkStack extends cdk.Stack {
  public readonly vpc: ec2.Vpc;
  public readonly backendSecurityGroup: ec2.SecurityGroup;
  public readonly databaseSecurityGroup: ec2.SecurityGroup;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create VPC with public and private subnets
    this.vpc = new ec2.Vpc(this, 'CommanderAiVpc', {
      maxAzs: 3,  // Multi-AZ for high availability
      natGateways: 2,  // NAT for private subnets
      subnetConfiguration: [
        {
          name: 'Public',
          subnetType: ec2.SubnetType.PUBLIC,
          cidrMask: 24,
        },
        {
          name: 'Private',
          subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
          cidrMask: 24,
        },
        {
          name: 'Isolated',
          subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
          cidrMask: 24,
        },
      ],
    });

    // Security group for backend API
    this.backendSecurityGroup = new ec2.SecurityGroup(this, 'BackendSG', {
      vpc: this.vpc,
      description: 'Security group for FastAPI backend',
      allowAllOutbound: true,
    });

    // Security group for databases
    this.databaseSecurityGroup = new ec2.SecurityGroup(this, 'DatabaseSG', {
      vpc: this.vpc,
      description: 'Security group for RDS and ElastiCache',
      allowAllOutbound: false,
    });

    // Allow backend to access databases
    this.databaseSecurityGroup.addIngressRule(
      this.backendSecurityGroup,
      ec2.Port.tcp(5432),
      'PostgreSQL from backend'
    );

    this.databaseSecurityGroup.addIngressRule(
      this.backendSecurityGroup,
      ec2.Port.tcp(6379),
      'Redis from backend'
    );

    // Output VPC ID
    new cdk.CfnOutput(this, 'VpcId', {
      value: this.vpc.vpcId,
      description: 'VPC ID',
    });
  }
}
```

### 2. Database Stack

```typescript
// lib/database-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

export interface DatabaseStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
  securityGroup: ec2.SecurityGroup;
}

export class DatabaseStack extends cdk.Stack {
  public readonly dbInstance: rds.DatabaseInstance;
  public readonly dbSecret: secretsmanager.Secret;

  constructor(scope: Construct, id: string, props: DatabaseStackProps) {
    super(scope, id, props);

    // Create database credentials secret
    this.dbSecret = new secretsmanager.Secret(this, 'DBSecret', {
      generateSecretString: {
        secretStringTemplate: JSON.stringify({ username: 'commander' }),
        generateStringKey: 'password',
        excludePunctuation: true,
        includeSpace: false,
      },
    });

    // Parameter group with pgvector extension
    const parameterGroup = new rds.ParameterGroup(this, 'DBParameterGroup', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16,
      }),
      parameters: {
        'shared_preload_libraries': 'vector',
      },
    });

    // Create RDS PostgreSQL instance
    this.dbInstance = new rds.DatabaseInstance(this, 'PostgresDB', {
      engine: rds.DatabaseInstanceEngine.postgres({
        version: rds.PostgresEngineVersion.VER_16,
      }),
      instanceType: ec2.InstanceType.of(
        ec2.InstanceClass.T4G,
        ec2.InstanceSize.MEDIUM
      ),
      vpc: props.vpc,
      vpcSubnets: {
        subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
      },
      securityGroups: [props.securityGroup],
      credentials: rds.Credentials.fromSecret(this.dbSecret),
      databaseName: 'commander_ai',
      allocatedStorage: 100,
      maxAllocatedStorage: 500,  // Auto-scaling storage
      multiAz: true,  // High availability
      backupRetention: cdk.Duration.days(7),
      deleteAutomatedBackups: false,
      removalPolicy: cdk.RemovalPolicy.SNAPSHOT,
      parameterGroup: parameterGroup,
    });

    // Output database endpoint
    new cdk.CfnOutput(this, 'DBEndpoint', {
      value: this.dbInstance.dbInstanceEndpointAddress,
      description: 'PostgreSQL endpoint',
    });

    new cdk.CfnOutput(this, 'DBSecretArn', {
      value: this.dbSecret.secretArn,
      description: 'Database credentials secret ARN',
    });
  }
}
```

### 3. Cache Stack (Redis)

```typescript
// lib/cache-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as elasticache from 'aws-cdk-lib/aws-elasticache';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import { Construct } from 'constructs';

export interface CacheStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
  securityGroup: ec2.SecurityGroup;
}

export class CacheStack extends cdk.Stack {
  public readonly redisCluster: elasticache.CfnReplicationGroup;

  constructor(scope: Construct, id: string, props: CacheStackProps) {
    super(scope, id, props);

    // Create subnet group
    const subnetGroup = new elasticache.CfnSubnetGroup(this, 'RedisSubnetGroup', {
      description: 'Subnet group for Redis',
      subnetIds: props.vpc.selectSubnets({
        subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS,
      }).subnetIds,
    });

    // Create Redis cluster
    this.redisCluster = new elasticache.CfnReplicationGroup(this, 'RedisCluster', {
      replicationGroupDescription: 'Commander.ai Redis cluster',
      engine: 'redis',
      engineVersion: '7.1',
      cacheNodeType: 'cache.t4g.medium',
      numCacheClusters: 2,  // Primary + 1 replica
      automaticFailoverEnabled: true,
      multiAzEnabled: true,
      cacheSubnetGroupName: subnetGroup.ref,
      securityGroupIds: [props.securityGroup.securityGroupId],
      atRestEncryptionEnabled: true,
      transitEncryptionEnabled: true,
      snapshotRetentionLimit: 5,
    });

    // Output Redis endpoint
    new cdk.CfnOutput(this, 'RedisEndpoint', {
      value: this.redisCluster.attrPrimaryEndPointAddress,
      description: 'Redis primary endpoint',
    });
  }
}
```

### 4. Backend Stack (FastAPI on ECS)

```typescript
// lib/backend-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecr from 'aws-cdk-lib/aws-ecr';
import * as secretsmanager from 'aws-cdk-lib/aws-secretsmanager';
import { Construct } from 'constructs';

export interface BackendStackProps extends cdk.StackProps {
  vpc: ec2.Vpc;
  securityGroup: ec2.SecurityGroup;
  dbSecret: secretsmanager.Secret;
  dbEndpoint: string;
  redisEndpoint: string;
}

export class BackendStack extends cdk.Stack {
  public readonly service: ecs_patterns.ApplicationLoadBalancedFargateService;

  constructor(scope: Construct, id: string, props: BackendStackProps) {
    super(scope, id, props);

    // Create ECS cluster
    const cluster = new ecs.Cluster(this, 'BackendCluster', {
      vpc: props.vpc,
      containerInsights: true,
    });

    // Create Fargate service with ALB
    this.service = new ecs_patterns.ApplicationLoadBalancedFargateService(
      this,
      'BackendService',
      {
        cluster,
        cpu: 1024,  // 1 vCPU
        memoryLimitMiB: 2048,  // 2 GB
        desiredCount: 2,  // Multi-instance for HA
        taskImageOptions: {
          image: ecs.ContainerImage.fromAsset('../../', {
            file: 'infrastructure/docker/backend.Dockerfile',
          }),
          containerPort: 8000,
          environment: {
            ENVIRONMENT: 'production',
            DATABASE_URL: `postgresql+asyncpg://commander:PASSWORD@${props.dbEndpoint}:5432/commander_ai`,
            REDIS_URL: `redis://${props.redisEndpoint}:6379/0`,
          },
          secrets: {
            OPENAI_API_KEY: ecs.Secret.fromSecretsManager(
              secretsmanager.Secret.fromSecretNameV2(this, 'OpenAIKey', 'commander-ai/openai')
            ),
            TAVILY_API_KEY: ecs.Secret.fromSecretsManager(
              secretsmanager.Secret.fromSecretNameV2(this, 'TavilyKey', 'commander-ai/tavily')
            ),
            DB_PASSWORD: ecs.Secret.fromSecretsManager(props.dbSecret, 'password'),
            // JWT Authentication secrets (required for production)
            SECRET_KEY: ecs.Secret.fromSecretsManager(
              secretsmanager.Secret.fromSecretNameV2(this, 'JWTSecret', 'commander-ai/jwt-secret')
            ),
            // Optional: Override default token expiry
            // ACCESS_TOKEN_EXPIRE_MINUTES: '60',
            // REFRESH_TOKEN_EXPIRE_DAYS: '7',
          },
        },
        publicLoadBalancer: true,
        healthCheckGracePeriod: cdk.Duration.seconds(60),
      }
    );

    // Configure auto-scaling
    const scaling = this.service.service.autoScaleTaskCount({
      minCapacity: 2,
      maxCapacity: 10,
    });

    scaling.scaleOnCpuUtilization('CpuScaling', {
      targetUtilizationPercent: 70,
      scaleInCooldown: cdk.Duration.seconds(60),
      scaleOutCooldown: cdk.Duration.seconds(60),
    });

    // Output ALB URL
    new cdk.CfnOutput(this, 'BackendUrl', {
      value: this.service.loadBalancer.loadBalancerDnsName,
      description: 'Backend API URL',
    });
  }
}
```

### 5. Frontend Stack (S3 + CloudFront)

```typescript
// lib/frontend-stack.ts
import * as cdk from 'aws-cdk-lib';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import { Construct } from 'constructs';

export class FrontendStack extends cdk.Stack {
  public readonly distribution: cloudfront.Distribution;

  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // Create S3 bucket for frontend
    const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
      encryption: s3.BucketEncryption.S3_MANAGED,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // Create CloudFront distribution
    this.distribution = new cloudfront.Distribution(this, 'Distribution', {
      defaultBehavior: {
        origin: new origins.S3Origin(websiteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html',
          ttl: cdk.Duration.seconds(0),
        },
      ],
    });

    // Deploy frontend files
    new s3deploy.BucketDeployment(this, 'DeployWebsite', {
      sources: [s3deploy.Source.asset('../../frontend/out')],
      destinationBucket: websiteBucket,
      distribution: this.distribution,
      distributionPaths: ['/*'],
    });

    // Output CloudFront URL
    new cdk.CfnOutput(this, 'CloudFrontUrl', {
      value: this.distribution.distributionDomainName,
      description: 'Frontend URL',
    });
  }
}
```

---

## 🚢 Deployment Steps

### 1. Set Up Secrets

```bash
# Store API keys in AWS Secrets Manager
aws secretsmanager create-secret \
  --name commander-ai/openai \
  --secret-string '{"api_key":"sk-..."}'

aws secretsmanager create-secret \
  --name commander-ai/tavily \
  --secret-string '{"api_key":"tvly-..."}'

# JWT Authentication secret (required for production)
# Generate a secure random key: openssl rand -hex 32
aws secretsmanager create-secret \
  --name commander-ai/jwt-secret \
  --secret-string '{"secret_key":"<your-generated-secret-key>"}'
```

**⚠️ Authentication Security:**
- Generate a strong random secret for JWT signing: `openssl rand -hex 32`
- **Never** commit the secret key to version control
- Rotate secrets periodically (recommended: every 90 days)
- For development, use the MVP user bypass (no JWT needed)
- For production, enforce JWT authentication by removing MVP user bypass

### 2. Build and Push Docker Images

```bash
# Build backend image
docker build -f infrastructure/docker/backend.Dockerfile -t commander-ai-backend .

# Tag and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com
docker tag commander-ai-backend:latest <account-id>.dkr.ecr.us-east-1.amazonaws.com/commander-ai-backend:latest
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/commander-ai-backend:latest
```

### 3. Deploy with CDK

```bash
cd infrastructure/cdk

# Bootstrap CDK (first time only)
cdk bootstrap

# Synthesize CloudFormation templates
cdk synth

# Deploy all stacks
cdk deploy --all

# Or deploy specific stacks in order
cdk deploy NetworkStack
cdk deploy DatabaseStack
cdk deploy CacheStack
cdk deploy BackendStack
cdk deploy FrontendStack
```

### 4. Run Database Migrations

```bash
# Connect to RDS via bastion host or VPN
alembic upgrade head
```

### 5. Verify Deployment

```bash
# Get backend URL
aws cloudformation describe-stacks \
  --stack-name BackendStack \
  --query 'Stacks[0].Outputs[?OutputKey==`BackendUrl`].OutputValue' \
  --output text

# Test API
curl https://<backend-url>/health
```

---

## 💰 Cost Optimization

### Monthly Cost Estimate (Production)

| Service | Configuration | Estimated Cost |
|---------|--------------|----------------|
| ECS Fargate (Backend) | 2 tasks, 1vCPU, 2GB | $60 |
| ECS Fargate (Qdrant) | 1 task, 2vCPU, 4GB | $60 |
| RDS PostgreSQL | db.t4g.medium, Multi-AZ | $120 |
| ElastiCache Redis | cache.t4g.medium, 2 nodes | $80 |
| S3 + CloudFront | 100GB storage, 1TB transfer | $30 |
| NAT Gateway | 2 gateways | $90 |
| Data Transfer | Inter-AZ, Outbound | $50 |
| **Total** | | **~$490/month** |

### Cost Reduction Strategies

1. **Development Environment**:
   ```typescript
   // Use smaller instance types
   instanceType: ec2.InstanceType.of(
     ec2.InstanceClass.T4G,
     ec2.InstanceSize.SMALL  // Instead of MEDIUM
   )

   // Single-AZ for dev
   multiAz: false,
   desiredCount: 1,
   ```

2. **Reserved Instances**:
   - 40% savings with 1-year reservation
   - 60% savings with 3-year reservation

3. **Spot Instances**:
   ```typescript
   capacityProviderStrategies: [{
     capacityProvider: 'FARGATE_SPOT',
     weight: 1,
   }]
   ```

4. **Auto-scaling**:
   ```typescript
   // Scale down during off-hours
   scaling.scaleOnSchedule('ScaleDown', {
     schedule: autoscaling.Schedule.cron({
       hour: '22',
       minute: '0',
     }),
     minCapacity: 1,
     maxCapacity: 1,
   });
   ```

---

## 🔒 Security Best Practices

### 1. Network Security

```typescript
// No public access to databases
vpcSubnets: {
  subnetType: ec2.SubnetType.PRIVATE_ISOLATED,
}

// Restrict security group rules
databaseSecurityGroup.addIngressRule(
  backendSecurityGroup,
  ec2.Port.tcp(5432),
  'PostgreSQL from backend only'
);
```

### 2. Encryption

```typescript
// Database encryption at rest
storageEncrypted: true,

// Redis encryption
atRestEncryptionEnabled: true,
transitEncryptionEnabled: true,

// S3 bucket encryption
encryption: s3.BucketEncryption.S3_MANAGED,
```

### 3. Secrets Management

```typescript
// Use Secrets Manager, not environment variables
secrets: {
  OPENAI_API_KEY: ecs.Secret.fromSecretsManager(openAISecret),
  DB_PASSWORD: ecs.Secret.fromSecretsManager(dbSecret, 'password'),
}
```

### 4. IAM Least Privilege

```typescript
// Task role with minimal permissions
const taskRole = new iam.Role(this, 'TaskRole', {
  assumedBy: new iam.ServicePrincipal('ecs-tasks.amazonaws.com'),
  managedPolicies: [
    iam.ManagedPolicy.fromAwsManagedPolicyName('CloudWatchLogsFullAccess'),
  ],
});

// Grant specific secrets access
openAISecret.grantRead(taskRole);
```

---

## 📊 Monitoring & Logging

### CloudWatch Dashboards

```typescript
// lib/monitoring-stack.ts
const dashboard = new cloudwatch.Dashboard(this, 'Dashboard', {
  dashboardName: 'CommanderAI-Metrics',
});

// Add widgets
dashboard.addWidgets(
  new cloudwatch.GraphWidget({
    title: 'API Requests',
    left: [
      backendService.targetGroup.metrics.requestCount(),
      backendService.targetGroup.metrics.targetResponseTime(),
    ],
  }),
  new cloudwatch.GraphWidget({
    title: 'Database Connections',
    left: [dbInstance.metricDatabaseConnections()],
  })
);
```

### CloudWatch Alarms

```typescript
// High error rate alarm
const errorAlarm = new cloudwatch.Alarm(this, 'HighErrorRate', {
  metric: backendService.targetGroup.metrics.httpCodeTarget(
    lb.HttpCodeTarget.TARGET_5XX_COUNT
  ),
  threshold: 10,
  evaluationPeriods: 2,
  treatMissingData: cloudwatch.TreatMissingData.NOT_BREACHING,
});

// SNS notification
const topic = new sns.Topic(this, 'AlarmTopic');
topic.addSubscription(new subscriptions.EmailSubscription('alerts@example.com'));
errorAlarm.addAlarmAction(new cloudwatch_actions.SnsAction(topic));
```

---

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/deploy.yml
name: Deploy to AWS

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1

      - name: Build frontend
        run: |
          cd frontend
          npm install
          npm run build

      - name: Build and push Docker image
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_REGISTRY
          docker build -f infrastructure/docker/backend.Dockerfile -t commander-ai-backend .
          docker tag commander-ai-backend:latest $ECR_REGISTRY/commander-ai-backend:latest
          docker push $ECR_REGISTRY/commander-ai-backend:latest

      - name: Deploy CDK stacks
        run: |
          cd infrastructure/cdk
          npm install
          npx cdk deploy --all --require-approval never
```

---

## 🌍 Multi-Region Deployment

### Global Architecture

```typescript
// Deploy to multiple regions for disaster recovery
const regions = ['us-east-1', 'eu-west-1', 'ap-southeast-1'];

regions.forEach(region => {
  new BackendStack(app, `BackendStack-${region}`, {
    env: { region },
  });
});

// Use Route 53 for geo-routing
const hostedZone = route53.HostedZone.fromLookup(this, 'Zone', {
  domainName: 'commander-ai.com',
});

new route53.ARecord(this, 'GlobalAlias', {
  zone: hostedZone,
  target: route53.RecordTarget.fromAlias(
    new targets.CloudFrontTarget(distribution)
  ),
});
```

---

## 📝 Maintenance

### Database Backups

```typescript
// Automated backups
backupRetention: cdk.Duration.days(30),
preferredBackupWindow: '03:00-04:00',

// Manual snapshot before major changes
aws rds create-db-snapshot \
  --db-instance-identifier commander-ai-db \
  --db-snapshot-identifier pre-migration-$(date +%Y%m%d)
```

### Updates and Patches

```bash
# Update CDK dependencies
cd infrastructure/cdk
npm update

# Update Docker images
docker pull postgres:16
docker pull redis:7
docker pull qdrant/qdrant:latest

# Deploy updates
cdk deploy --all
```

---

## 🚨 Troubleshooting

### Common Issues

**1. Database connection failures**
```bash
# Check security groups
aws ec2 describe-security-groups --group-ids <sg-id>

# Test connectivity from backend
aws ecs execute-command \
  --cluster backend-cluster \
  --task <task-id> \
  --command "/bin/sh"
```

**2. ECS task keeps restarting**
```bash
# Check CloudWatch logs
aws logs tail /ecs/backend-service --follow

# Check task health
aws ecs describe-tasks \
  --cluster backend-cluster \
  --tasks <task-arn>
```

**3. High costs**
```bash
# Enable Cost Explorer
aws ce get-cost-and-usage \
  --time-period Start=2024-01-01,End=2024-01-31 \
  --granularity MONTHLY \
  --metrics "UnblendedCost"
```

---

## 📚 Additional Resources

- [AWS CDK Documentation](https://docs.aws.amazon.com/cdk/)
- [ECS Best Practices](https://docs.aws.amazon.com/AmazonECS/latest/bestpracticesguide/)
- [RDS Performance Insights](https://aws.amazon.com/rds/performance-insights/)
- [CloudWatch Container Insights](https://docs.aws.amazon.com/AmazonCloudWatch/latest/monitoring/ContainerInsights.html)

---

## 🤝 Contributing

Found ways to optimize the AWS deployment? Contributions welcome!

- 💡 Cost optimization strategies
- 🔒 Security enhancements
- 📊 Monitoring improvements
- 🚀 Performance tuning

---

**Status**: 🚀 Production-Ready AWS Architecture
**Last Updated**: February 2026
**Estimated Setup Time**: 2-3 hours
**Estimated Monthly Cost**: $490 (production), $150 (development)
