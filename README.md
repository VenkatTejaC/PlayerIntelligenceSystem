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

### ECS Direction

Recommended next step for ECS is AWS Fargate with either:

- one task definition containing both `api` and `ui` containers
- two separate ECS services if you want independent scaling later

For production, use environment variables or secrets in ECS rather than hardcoded values. For dataset access, prefer S3. For persistent Chroma storage, plan for EFS or another persistence strategy because container local storage is not durable.
