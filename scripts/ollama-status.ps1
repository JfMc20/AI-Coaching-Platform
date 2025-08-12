#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Check Ollama model status and manage downloads
#>

param(
    [ValidateSet("status", "resume", "test")]
    [string]$Action = "status"
)

Write-Host "🤖 Ollama Model Manager" -ForegroundColor Cyan
Write-Host ""

$OllamaContainer = "mvp-ollama"

if ($Action -eq "status") {
    Write-Host "📊 Model Status Check" -ForegroundColor Yellow
    Write-Host ""
    
    # Check listed models
    Write-Host "Listed Models:" -ForegroundColor Cyan
    docker exec $OllamaContainer ollama list
    Write-Host ""
    
    # Check manifests
    Write-Host "Available Manifests:" -ForegroundColor Cyan
    docker exec $OllamaContainer find /root/.ollama/models/manifests -name "*" -type f
    Write-Host ""
    
    # Check partial downloads
    Write-Host "Partial Downloads:" -ForegroundColor Cyan
    $partialFiles = docker exec $OllamaContainer find /root/.ollama/models/blobs -name "*partial*" -type f
    if ($partialFiles) {
        Write-Host "Found interrupted downloads:" -ForegroundColor Yellow
        docker exec $OllamaContainer ls -lh /root/.ollama/models/blobs/*partial* | Select-Object -First 5
        Write-Host "... (showing first 5 files)" -ForegroundColor Gray
    }
    else {
        Write-Host "No partial downloads found" -ForegroundColor Green
    }
    Write-Host ""
    
    # Check disk usage
    Write-Host "Disk Usage:" -ForegroundColor Cyan
    docker exec $OllamaContainer du -sh /root/.ollama/models
    Write-Host ""
    
    # Check background jobs
    Write-Host "Background Jobs:" -ForegroundColor Cyan
    $jobs = Get-Job | Where-Object { $_.Name -like "*Download*" -or $_.Name -like "*GPT*" }
    if ($jobs) {
        foreach ($job in $jobs) {
            Write-Host "  $($job.Name): $($job.State)" -ForegroundColor Gray
        }
    }
    else {
        Write-Host "  No background jobs" -ForegroundColor Gray
    }
}

if ($Action -eq "resume") {
    Write-Host "🔄 Resuming Model Downloads" -ForegroundColor Yellow
    Write-Host ""
    
    # Check if job already exists
    $existingJob = Get-Job -Name "GPT_OSS_Download" -ErrorAction SilentlyContinue
    if ($existingJob) {
        Write-Host "Download job already exists: $($existingJob.State)" -ForegroundColor Yellow
        
        if ($existingJob.State -eq "Completed") {
            Write-Host "Getting job results..." -ForegroundColor Cyan
            $result = Receive-Job -Job $existingJob
            Write-Host $result -ForegroundColor Gray
            Remove-Job -Job $existingJob
        }
        elseif ($existingJob.State -eq "Running") {
            Write-Host "Job is still running. Monitor with: Get-Job -Name GPT_OSS_Download" -ForegroundColor Yellow
            return
        }
        else {
            Write-Host "Removing old job and starting new one..." -ForegroundColor Yellow
            Remove-Job -Job $existingJob
        }
    }
    
    Write-Host "Starting background download of gpt-oss:20b..." -ForegroundColor Green
    
    $job = Start-Job -Name "GPT_OSS_Download" -ScriptBlock {
        param($Container)
        
        Write-Output "=== Starting gpt-oss:20b download ==="
        Write-Output "Time: $(Get-Date)"
        
        try {
            $result = docker exec $Container ollama pull "gpt-oss:20b"
            Write-Output "=== Download completed ==="
            Write-Output "Time: $(Get-Date)"
            Write-Output $result
            return "SUCCESS"
        }
        catch {
            Write-Output "=== Download failed ==="
            Write-Output "Error: $($_.Exception.Message)"
            return "FAILED"
        }
    } -ArgumentList $OllamaContainer
    
    Write-Host "✅ Background job started (ID: $($job.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "Monitor with:" -ForegroundColor Yellow
    Write-Host "  Get-Job -Name GPT_OSS_Download" -ForegroundColor Gray
    Write-Host "  Receive-Job -Name GPT_OSS_Download -Keep" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Check status with:" -ForegroundColor Yellow
    Write-Host "  .\scripts\ollama-status.ps1 -Action status" -ForegroundColor Gray
}

if ($Action -eq "test") {
    Write-Host "🧪 Testing AI Models" -ForegroundColor Yellow
    Write-Host ""
    
    try {
        Write-Host "Checking AI Engine status..." -ForegroundColor Cyan
        $response = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/models/status" -Method GET -TimeoutSec 10
        $status = $response.Content | ConvertFrom-Json
        
        Write-Host "Embedding Model: $($status.embedding_model.name) - $($status.embedding_model.status)" -ForegroundColor Gray
        Write-Host "Chat Model: $($status.chat_model.name) - $($status.chat_model.status)" -ForegroundColor Gray
        Write-Host ""
        
        if ($status.embedding_model.loaded) {
            Write-Host "Testing embeddings..." -ForegroundColor Cyan
            $embTest = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/ollama/test-embedding" -Method POST -TimeoutSec 30
            Write-Host "✅ Embedding test passed" -ForegroundColor Green
        }
        
        if ($status.chat_model.loaded) {
            Write-Host "Testing chat..." -ForegroundColor Cyan
            $chatTest = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/ollama/test-chat" -Method POST -TimeoutSec 60
            Write-Host "✅ Chat test passed" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ Test failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Done" -ForegroundColor Green