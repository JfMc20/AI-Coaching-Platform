#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Run the Authentication Service for development

.DESCRIPTION
    This script starts the Authentication Service with proper environment configuration
    for local development. It sets up the required environment variables and starts
    the FastAPI server with hot reload enabled.

.EXAMPLE
    .\scripts\run-auth-service.ps1
    
.EXAMPLE
    .\scripts\run-auth-service.ps1 -Port 8001 -Host "0.0.0.0"
#>

param(
    [int]$Port = 8001,
    [string]$Host = "127.0.0.1",
    [switch]$Reload = $true,
    [string]$LogLevel = "info"
)

# Set script location
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectRoot = Split-Path -Parent $ScriptDir

# Load environment variables from .env file if it exists
$EnvFile = Join-Path $ProjectRoot ".env"
if (Test-Path $EnvFile) {
    Write-Host "Loading environment variables from .env file..." -ForegroundColor Green
    Get-Content $EnvFile | ForEach-Object {
        if ($_ -match "^([^#][^=]+)=(.*)$") {
            $name = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($name, $value, "Process")
            Write-Host "  $name = $value" -ForegroundColor Gray
        }
    }
} else {
    Write-Warning ".env file not found at $EnvFile"
}

# Set required environment variables if not already set
$RequiredEnvVars = @{
    "PYTHONPATH" = $ProjectRoot
    "JWT_SECRET_KEY" = "dev-secret-key-change-in-production"
    "DATABASE_URL" = "postgresql://user:password@localhost:5432/mvp_coaching_ai"
}

foreach ($envVar in $RequiredEnvVars.GetEnumerator()) {
    if (-not [Environment]::GetEnvironmentVariable($envVar.Key, "Process")) {
        Write-Host "Setting $($envVar.Key) = $($envVar.Value)" -ForegroundColor Yellow
        [Environment]::SetEnvironmentVariable($envVar.Key, $envVar.Value, "Process")
    }
}

# Change to auth service directory
$AuthServiceDir = Join-Path $ProjectRoot "services" "auth-service"
Set-Location $AuthServiceDir

Write-Host "Starting Authentication Service..." -ForegroundColor Green
Write-Host "  Host: $Host" -ForegroundColor Gray
Write-Host "  Port: $Port" -ForegroundColor Gray
Write-Host "  Reload: $Reload" -ForegroundColor Gray
Write-Host "  Log Level: $LogLevel" -ForegroundColor Gray
Write-Host ""

# Start the FastAPI server
$ReloadFlag = if ($Reload) { "--reload" } else { "" }

try {
    if ($Reload) {
        uvicorn app.main:app --host $Host --port $Port --reload --log-level $LogLevel
    } else {
        uvicorn app.main:app --host $Host --port $Port --log-level $LogLevel
    }
} catch {
    Write-Error "Failed to start Authentication Service: $_"
    exit 1
}