## Player Intelligence System

This project includes Docker assets for running the FastAPI backend and Streamlit UI locally with Docker Desktop, then tagging those images for Amazon ECR and later ECS deployment.

### Services

- `api`: FastAPI service exposed on `http://localhost:8000`
- `ui`: Streamlit service exposed on `http://localhost:8501`

### Local Docker Run

Build and start both services:

```powershell
docker compose build
docker compose up
```

Detached mode:

```powershell
docker compose up -d
```

Stop the stack:

```powershell
docker compose down
```

### Local Images

Compose builds these local images:

- `player-intelligence-api:local`
- `player-intelligence-ui:local`

### Runtime Configuration

The app reads runtime settings from environment variables. Useful variables include:

- `API_BASE_URL`
- `DATA_PATH`
- `MODEL_PATH`
- `CHROMA_PATH`
- `AWS_REGION`
- `S3_BUCKET`
- `S3_KEY`
- `S3_FALLBACK_TO_LOCAL`

### Tag For ECR

After building locally, tag the images for ECR:

```powershell
docker tag player-intelligence-api:local <account-id>.dkr.ecr.<aws-region>.amazonaws.com/player-intelligence-api:<tag>
docker tag player-intelligence-ui:local <account-id>.dkr.ecr.<aws-region>.amazonaws.com/player-intelligence-ui:<tag>
```

Then log in and push:

```powershell
aws ecr get-login-password --region <aws-region> | docker login --username AWS --password-stdin <account-id>.dkr.ecr.<aws-region>.amazonaws.com
docker push <account-id>.dkr.ecr.<aws-region>.amazonaws.com/player-intelligence-api:<tag>
docker push <account-id>.dkr.ecr.<aws-region>.amazonaws.com/player-intelligence-ui:<tag>
```

Or use the helper script:

```powershell
.\scripts\push-to-ecr.ps1 -AwsAccountId <account-id> -Region eu-west-2 -Tag latest
```

### ECS Direction

Recommended next step for ECS is AWS Fargate with either:

- one task definition containing both `api` and `ui` containers
- two separate ECS services if you want independent scaling later

For production, use environment variables or secrets in ECS rather than hardcoded values. For dataset access, prefer S3. For persistent Chroma storage, plan for EFS or another persistence strategy because container local storage is not durable.

### ECS Deployment Notes

An ECS Fargate task definition template is available at `deploy/ecs-task-definition.json`.

Recommended setup:

- Create two ECR repos: `player-intelligence-api` and `player-intelligence-ui`
- Push both local Docker images to ECR
- Register the ECS task definition after replacing placeholder account IDs
- Use an ECS task role with `s3:GetObject` permission on your dataset key
- Set `S3_FALLBACK_TO_LOCAL=false` in ECS so the API reads from S3 only

Example minimal IAM permission for the ECS task role:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": ["s3:GetObject"],
      "Resource": "arn:aws:s3:::player-intelligence-data/datasets/players.csv"
    }
  ]
}
```
