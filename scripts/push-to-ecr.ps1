param(
    [Parameter(Mandatory = $true)]
    [string]$AwsAccountId,

    [Parameter(Mandatory = $false)]
    [string]$Region = "eu-west-2",

    [Parameter(Mandatory = $false)]
    [string]$Tag = "latest"
)

$ErrorActionPreference = "Stop"

$registry = "$AwsAccountId.dkr.ecr.$Region.amazonaws.com"
$apiRepo = "player-intelligence-api"
$uiRepo = "player-intelligence-ui"

$apiLocalImage = "player-intelligence-api:local"
$uiLocalImage = "player-intelligence-ui:local"
$apiRemoteImage = "${registry}/${apiRepo}:${Tag}"
$uiRemoteImage = "${registry}/${uiRepo}:${Tag}"

Write-Host "Logging into ECR registry $registry"
aws ecr get-login-password --region $Region | docker login --username AWS --password-stdin $registry

Write-Host "Ensuring ECR repositories exist"
aws ecr describe-repositories --repository-names $apiRepo --region $Region *> $null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name $apiRepo --region $Region *> $null
}

aws ecr describe-repositories --repository-names $uiRepo --region $Region *> $null
if ($LASTEXITCODE -ne 0) {
    aws ecr create-repository --repository-name $uiRepo --region $Region *> $null
}

Write-Host "Tagging local images"
docker tag $apiLocalImage $apiRemoteImage
docker tag $uiLocalImage $uiRemoteImage

Write-Host "Pushing API image: $apiRemoteImage"
docker push $apiRemoteImage

Write-Host "Pushing UI image: $uiRemoteImage"
docker push $uiRemoteImage

Write-Host "Done."
Write-Host "API image: $apiRemoteImage"
Write-Host "UI image:  $uiRemoteImage"
