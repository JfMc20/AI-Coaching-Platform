#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Check Ollama model status and manage downloads
.DESCRIPTION
    Simple script to check model status and resume downloads
#>

param(
    [ValidateSet("status", "resume", "test")]
    [string]$Action = "status"
)

Write-Host "🤖 Ollama Model Status Checker" -ForegroundColor Cyan
Write-Host ""

$OllamaContainer = "mvp-ollama"

function Show-ModelStatus {
    Write-Host "📊 Checking Model Status..." -ForegroundColor Yellow
    Write-Host ""
    
    # Check what models are listed
    Write-Host "Listed Models:" -ForegroundColor Cyan
    try {
        $listedModels = docker exec $OllamaContainer ollama list
        Write-Host $listedModels -ForegroundColor Gray
    }
    catch {
        Write-Host "Error getting model list: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Check manifests
    Write-Host "Available Manifests:" -ForegroundColor Cyan
    try {
        $manifests = docker exec $OllamaContainer find /root/.ollama/models/manifests -name "*" -type f
        foreach ($manifest in $manifests) {
            Write-Host "  $manifest" -ForegroundColor Gray
        }
    }
    catch {
        Write-Host "Error checking manifests: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Check for partial downloads
    Write-Host "Partial Downloads:" -ForegroundColor Cyan
    try {
        $partialFiles = docker exec $OllamaContainer find /root/.ollama/models/blobs -name "*partial*" -type f
        if ($partialFiles) {
            Write-Host "Found partial downloads:" -ForegroundColor Yellow
            foreach ($file in $partialFiles) {
                $size = docker exec $OllamaContainer ls -lh $file
                Write-Host "  $size" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "  No partial downloads found" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "Error checking partial downloads: $($_.Exception.Message)" -ForegroundColor Red
    }
    
    Write-Host ""
    
    # Check disk usage
    Write-Host "Disk Usage:" -ForegroundColor Cyan
    try {
        $diskUsage = docker exec $OllamaContainer du -sh /root/.ollama/models
        Write-Host "  $diskUsage" -ForegroundColor Gray
    }
    catch {
        Write-Host "Error checking disk usage: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Resume-Downloads {
    Write-Host "🔄 Resuming Model Downloads..." -ForegroundColor Yellow
    Write-Host ""
    
    # Try to resume gpt-oss:20b download
    Write-Host "Attempting to resume gpt-oss:20b download..." -ForegroundColor Cyan
    
    # Start background job for download
    $jobName = "GPT_OSS_Download"
    
    # Check if job already exists
    $existingJob = Get-Job -Name $jobName -ErrorAction SilentlyContinue
    if ($existingJob) {
        Write-Host "Download job already running: $($existingJob.State)" -ForegroundColor Yellow
        if ($existingJob.State -eq "Completed") {
            $result = Receive-Job -Job $existingJob
            Write-Host "Previous job result: $result" -ForegroundColor Gray
            Remove-Job -Job $existingJob
        }
        elseif ($existingJob.State -eq "Failed") {
            Write-Host "Previous job failed, removing and starting new one..." -ForegroundColor Yellow
            Remove-Job -Job $existingJob
        }
        else {
            Write-Host "Job is still running. Use Get-Job to monitor." -ForegroundColor Yellow
            return
        }
    }
    
    # Start new background job
    Write-Host "Starting background download job..." -ForegroundColor Green
    
    $job = Start-Job -Name $jobName -ScriptBlock {
        param($Container)
        
        $output = @()
        $output += "Starting download of gpt-oss:20b..."
        
        try {
            # Try to pull the model
            $result = docker exec $Container ollama pull "gpt-oss:20b" 2>&1
            $output += $result
            
            if ($LASTEXITCODE -eq 0) {
                $output += "Download completed successfully!"
                return @{
                    Success = $true
                    Output = $output
                }
            }
            else {
                $output += "Download failed with exit code: $LASTEXITCODE"
                return @{
                    Success = $false
                    Output = $output
                }
            }
        }
        catch {
            $output += "Exception: $($_.Exception.Message)"
            return @{
                Success = $false
                Output = $output
            }
        }
    } -ArgumentList $OllamaContainer
    
    Write-Host "✅ Background job started (Job ID: $($job.Id))" -ForegroundColor Green
    Write-Host ""
    Write-Host "💡 Monitor progress with:" -ForegroundColor Yellow
    Write-Host "   Get-Job -Name $jobName" -ForegroundColor Gray
    Write-Host "   Receive-Job -Name $jobName -Keep" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 Check final result with:" -ForegroundColor Yellow
    Write-Host "   .\scripts\check-ollama-models.ps1 -Action status" -ForegroundColor Gray
}

function Test-Models {
    Write-Host "🧪 Testing Models via AI Engine..." -ForegroundColor Yellow
    Write-Host ""
    
    try {
        # Test model status endpoint
        Write-Host "Checking AI Engine model status..." -ForegroundColor Cyan
        $response = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/models/status" -Method GET -TimeoutSec 10
        $status = $response.Content | ConvertFrom-Json
        
        Write-Host "Embedding Model: $($status.embedding_model.name) - Status: $($status.embedding_model.status)" -ForegroundColor Gray
        Write-Host "Chat Model: $($status.chat_model.name) - Status: $($status.chat_model.status)" -ForegroundColor Gray
        Write-Host ""
        
        # Test embedding if available
        if ($status.embedding_model.loaded) {
            Write-Host "Testing embedding generation..." -ForegroundColor Cyan
            try {
                $embeddingTest = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/ollama/test-embedding" -Method POST -TimeoutSec 30
                Write-Host "✅ Embedding test passed" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Embedding test failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "⚠️ Embedding model not loaded, skipping test" -ForegroundColor Yellow
        }
        
        # Test chat if available
        if ($status.chat_model.loaded) {
            Write-Host "Testing chat generation..." -ForegroundColor Cyan
            try {
                $chatTest = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/ollama/test-chat" -Method POST -TimeoutSec 60
                Write-Host "✅ Chat test passed" -ForegroundColor Green
            }
            catch {
                Write-Host "❌ Chat test failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        else {
            Write-Host "⚠️ Chat model not loaded, skipping test" -ForegroundColor Yellow
        }
    }
    catch {
        Write-Host "❌ Failed to connect to AI Engine: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-Jobs {
    Write-Host "📋 Background Jobs:" -ForegroundColor Yellow
    
    $jobs = Get-Job | Where-Object { $_.Name -like "*Download*" -or $_.Name -like "*GPT*" }
    
    if ($jobs) {
        foreach ($job in $jobs) {
            Write-Host "  Job: $($job.Name) - State: $($job.State)" -ForegroundColor Gray
            
            if ($job.State -eq "Completed") {
                Write-Host "    ✅ Job completed - use Receive-Job to see results" -ForegroundColor Green
            }
            elseif ($job.State -eq "Failed") {
                Write-Host "    ❌ Job failed" -ForegroundColor Red
            }
            elseif ($job.State -eq "Running") {
                Write-Host "    🔄 Job is running..." -ForegroundColor Cyan
            }
        }
    }
    else {
        Write-Host "  No background jobs found" -ForegroundColor Gray
    }
}

function Show-Jobs {
    Write-Host "📋 Background Jobs:" -ForegroundColor Yellow
    
    $jobs = Get-Job | Where-Object { $_.Name -like "*Download*" -or $_.Name -like "*GPT*" }
    
    if ($jobs) {
        foreach ($job in $jobs) {
            Write-Host "  Job: $($job.Name) - State: $($job.State)" -ForegroundColor Gray
            
            if ($job.State -eq "Completed") {
                Write-Host "    ✅ Job completed - use Receive-Job to see results" -ForegroundColor Green
            }
            elseif ($job.State -eq "Failed") {
                Write-Host "    ❌ Job failed" -ForegroundColor Red
            }
            elseif ($job.State -eq "Running") {
                Write-Host "    🔄 Job is running..." -ForegroundColor Cyan
            }
        }
    }
    else {
        Write-Host "  No background jobs found" -ForegroundColor Gray
    }
}

# Main execution
switch ($Action) {
    "status" {
        Show-ModelStatus
        Write-Host ""
        Show-Jobs
    }
    
    "resume" {
        Resume-Downloads
    }
    
    "test" {
        Test-Models
    }
}

Write-Host ""
Write-Host "🏁 Done" -ForegroundColor Green