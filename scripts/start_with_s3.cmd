@echo off
setlocal EnableExtensions EnableDelayedExpansion

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "REPO_ROOT=%%~fI"
set "ENV_FILE=%REPO_ROOT%\.env.local"
set "PYTHON_EXE=%REPO_ROOT%\.venv\Scripts\python.exe"

if not exist "%ENV_FILE%" (
    echo Missing %ENV_FILE%
    echo Create it from .env.local.example with your temporary AWS credentials.
    exit /b 1
)

if not exist "%PYTHON_EXE%" (
    echo Missing virtual environment Python at %PYTHON_EXE%
    exit /b 1
)

for /f "usebackq tokens=1,* delims==" %%A in ("%ENV_FILE%") do (
    set "KEY=%%A"
    set "VALUE=%%B"
    if defined KEY (
        if not "!KEY:~0,1!"=="#" (
            set "!KEY!=!VALUE!"
        )
    )
)

if "%AWS_ACCESS_KEY_ID%"=="" (
    echo AWS_ACCESS_KEY_ID is missing from .env.local
    exit /b 1
)

if "%AWS_SECRET_ACCESS_KEY%"=="" (
    echo AWS_SECRET_ACCESS_KEY is missing from .env.local
    exit /b 1
)

if "%AWS_SESSION_TOKEN%"=="" (
    echo AWS_SESSION_TOKEN is missing from .env.local
    exit /b 1
)

if "%AWS_DEFAULT_REGION%"=="" (
    set "AWS_DEFAULT_REGION=eu-west-2"
)

cd /d "%REPO_ROOT%"

echo Verifying AWS credentials against S3...
aws sts get-caller-identity >nul
if errorlevel 1 (
    echo AWS identity check failed. Update .env.local with fresh temporary credentials.
    exit /b 1
)

aws s3 ls s3://player-intelligence-data/datasets/ >nul
if errorlevel 1 (
    echo S3 access check failed. Verify .env.local credentials and bucket permissions.
    exit /b 1
)

echo Starting backend with S3 credentials loaded...
start "Player Intelligence Backend" cmd /k "cd /d %REPO_ROOT% && set AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID% && set AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY% && set AWS_SESSION_TOKEN=%AWS_SESSION_TOKEN% && set AWS_DEFAULT_REGION=%AWS_DEFAULT_REGION% && %PYTHON_EXE% -m uvicorn backend.api:app --reload"

echo Starting frontend with same S3 credentials...
start "Player Intelligence Frontend" cmd /k "cd /d %REPO_ROOT% && set AWS_ACCESS_KEY_ID=%AWS_ACCESS_KEY_ID% && set AWS_SECRET_ACCESS_KEY=%AWS_SECRET_ACCESS_KEY% && set AWS_SESSION_TOKEN=%AWS_SESSION_TOKEN% && set AWS_DEFAULT_REGION=%AWS_DEFAULT_REGION% && %PYTHON_EXE% -m streamlit run app/app.py"

echo Backend and frontend launch commands were started.
