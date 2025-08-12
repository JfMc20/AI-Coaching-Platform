#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Manage Ollama model downloads and status
.DESCRIPTION
    This script manages Ollama model downloads in background, checks status, and resumes interrupted downloads
.PARAMETER Action
    Action to perform: status, resume, download, test
.PARAMETER Model
    Model name to work with (optional)
.PARAMETER Background
    Run downloads in background (default: true)
#>

param(
    [ValidateSet("status", "resume", "download", "test", "cleanup")]
    [string]$Action = "status",
    [string]$Model = "",
    [bool]$Background = $true
)

Write-Host "🤖 Ollama Model Manager" -ForegroundColor Cyan
Write-Host "Action: $Action" -ForegroundColor Gray
Write-Host ""

# Configuration
$OllamaContainer = "mvp-ollama"
$RequiredModels = @(
    @{
        Name = "gpt-oss:20b"
        Type = "chat"
        Size = "~13.7GB"
        Priority = 1
    },
    @{
        Name = "nomic-embed-text"
        Type = "embedding"
        Size = "~274MB"
        Priority = 2
    }
)

function Get-ModelStatus {
    param([string]$ModelName)
    
    try {
        # Check if model is listed in Ollama
        $listResult = docker exec $OllamaContainer ollama list 2>$null
        $isListed = $listResult -match $ModelName.Replace(":", "\\s+")
        
        # Check if manifest exists
        $manifestPath = "/root/.ollama/models/manifests/registry.ollama.ai/library/$($ModelName.Replace(':', '/'))"
        docker exec $OllamaContainer test -f $manifestPath 2>$null
        $manifestExists = ($LASTEXITCODE -eq 0)
        
        # Check for partial downloads
        $partialFiles = docker exec $OllamaContainer find /root/.ollama/models/blobs -name "*partial*" 2>$null
        $hasPartialDownloads = $partialFiles.Count -gt 0
        
        return @{
            Name = $ModelName
            Listed = $isListed
            ManifestExists = $manifestExists
            HasPartialDownloads = $hasPartialDownloads
            Status = if ($isListed) { "Available" } elseif ($manifestExists -and $hasPartialDownloads) { "Downloading" } elseif ($manifestExists) { "Downloaded" } else { "Not Found" }
        }
    }
    catch {
        return @{
            Name = $ModelName
            Listed = $false
            ManifestExists = $false
            HasPartialDownloads = $false
            Status = "Error: $($_.Exception.Message)"
        }
    }
}

function Show-ModelStatus {
    Write-Host "📊 Model Status Report" -ForegroundColor Yellow
    Write-Host ""
    
    foreach ($model in $RequiredModels) {
        $status = Get-ModelStatus -ModelName $model.Name
        
        $statusColor = switch ($status.Status) {
            "Available" { "Green" }
            "Downloaded" { "Yellow" }
            "Downloading" { "Cyan" }
            "Not Found" { "Red" }
            default { "Red" }
        }
        
        Write-Host "  $($model.Name) ($($model.Size))" -ForegroundColor White
        Write-Host "    Status: $($status.Status)" -ForegroundColor $statusColor
        Write-Host "    Type: $($model.Type)" -ForegroundColor Gray
        Write-Host "    Listed: $($status.Listed)" -ForegroundColor Gray
        Write-Host "    Manifest: $($status.ManifestExists)" -ForegroundColor Gray
        Write-Host "    Partial Downloads: $($status.HasPartialDownloads)" -ForegroundColor Gray
        Write-Host ""
    }
    
    # Show disk usage
    try {
        $diskUsage = docker exec $OllamaContainer du -sh /root/.ollama/models 2>$null
        Write-Host "💾 Disk Usage: $diskUsage" -ForegroundColor Gray
    }
    catch {
        Write-Host "💾 Disk Usage: Unable to determine" -ForegroundColor Gray
    }
}

function Resume-ModelDownload {
    param([string]$ModelName)
    
    Write-Host "🔄 Resuming download for $ModelName..." -ForegroundColor Cyan
    
    $status = Get-ModelStatus -ModelName $ModelName
    
    if ($status.Status -eq "Available") {
        Write-Host "✅ Model $ModelName is already available" -ForegroundColor Green
        return $true
    }
    
    if ($status.Status -eq "Downloading" -or $status.ManifestExists) {
        Write-Host "📥 Attempting to resume download..." -ForegroundColor Yellow
        
        if ($Background) {
            # Start download in background
            $jobName = "OllamaDownload_$($ModelName.Replace(':', '_'))"
            
            # Check if job already exists
            $existingJob = Get-Job -Name $jobName -ErrorAction SilentlyContinue
            if ($existingJob) {
                Write-Host "⚠️ Download job already running: $($existingJob.State)" -ForegroundColor Yellow
                return $false
            }
            
            # Start background job
            $job = Start-Job -Name $jobName -ScriptBlock {
                param($Container, $Model)
                
                try {
                    $result = docker exec $Container ollama pull $Model 2>&1
                    return @{
                        Success = $LASTEXITCODE -eq 0
                        Output = $result
                        Model = $Model
                    }
                }
                catch {
                    return @{
                        Success = $false
                        Output = $_.Exception.Message
                        Model = $Model
                    }
                }
            } -ArgumentList $OllamaContainer, $ModelName
            
            Write-Host "🚀 Download started in background (Job ID: $($job.Id))" -ForegroundColor Green
            Write-Host "   Use 'Get-Job' to check status" -ForegroundColor Gray
            Write-Host "   Use 'Receive-Job -Id $($job.Id)' to see output" -ForegroundColor Gray
            
            return $true
        }
        else {
            # Synchronous download
            Write-Host "⏳ Starting synchronous download (this may take a while)..." -ForegroundColor Yellow
            
            try {
                $result = docker exec $OllamaContainer ollama pull $ModelName
                
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "✅ Download completed successfully" -ForegroundColor Green
                    return $true
                }
                else {
                    Write-Host "❌ Download failed" -ForegroundColor Red
                    Write-Host $result -ForegroundColor Red
                    return $false
                }
            }
            catch {
                Write-Host "❌ Download error: $($_.Exception.Message)" -ForegroundColor Red
                return $false
            }
        }
    }
    else {
        Write-Host "❌ Model $ModelName not found or not in downloadable state" -ForegroundColor Red
        return $false
    }
}

function Test-Models {
    Write-Host "🧪 Testing Model Functionality" -ForegroundColor Yellow
    Write-Host ""
    
    # Test via AI Engine service
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/models/status" -Method GET -TimeoutSec 10
        $status = $response.Content | ConvertFrom-Json
        
        Write-Host "📊 AI Engine Model Status:" -ForegroundColor Cyan
        Write-Host "  Embedding Model: $($status.embedding_model.name) - $($status.embedding_model.status)" -ForegroundColor Gray
        Write-Host "  Chat Model: $($status.chat_model.name) - $($status.chat_model.status)" -ForegroundColor Gray
        Write-Host ""
        
        # Test embedding if available
        if ($status.embedding_model.loaded) {
            Write-Host "🧠 Testing Embedding Generation..." -ForegroundColor Cyan
            try {
                $embeddingTest = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/ollama/test-embedding" -Method POST -TimeoutSec 30
                $embeddingResult = $embeddingTest.Content | ConvertFrom-Json
                Write-Host "  ✅ Embedding test passed - Generated $($embeddingResult.embeddings_count) embeddings" -ForegroundColor Green
            }
            catch {
                Write-Host "  ❌ Embedding test failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
        
        # Test chat if available
        if ($status.chat_model.loaded) {
            Write-Host "💬 Testing Chat Generation..." -ForegroundColor Cyan
            try {
                $chatTest = Invoke-WebRequest -Uri "http://localhost:8003/api/v1/ai/ollama/test-chat" -Method POST -TimeoutSec 60
                $chatResult = $chatTest.Content | ConvertFrom-Json
                Write-Host "  ✅ Chat test passed - Response length: $($chatResult.response.Length) chars" -ForegroundColor Green
            }
            catch {
                Write-Host "  ❌ Chat test failed: $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
    catch {
        Write-Host "❌ Failed to connect to AI Engine service: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Cleanup-PartialDownloads {
    Write-Host "🧹 Cleaning up partial downloads..." -ForegroundColor Yellow
    
    try {
        $partialFiles = docker exec $OllamaContainer find /root/.ollama/models/blobs -name "*partial*" 2>$null
        
        if ($partialFiles) {
            Write-Host "Found $($partialFiles.Count) partial files" -ForegroundColor Gray
            
            $confirmation = Read-Host "Do you want to delete partial downloads? This will require re-downloading models. (y/N)"
            if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
                docker exec $OllamaContainer find /root/.ollama/models/blobs -name "*partial*" -delete
                Write-Host "✅ Partial downloads cleaned up" -ForegroundColor Green
            }
            else {
                Write-Host "❌ Cleanup cancelled" -ForegroundColor Yellow
            }
        }
        else {
            Write-Host "✅ No partial downloads found" -ForegroundColor Green
        }
    }
    catch {
        Write-Host "❌ Cleanup failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

function Show-DownloadJobs {
    Write-Host "📋 Active Download Jobs" -ForegroundColor Yellow
    
    $jobs = Get-Job | Where-Object { $_.Name -like "OllamaDownload_*" }
    
    if ($jobs) {
        foreach ($job in $jobs) {
            $modelName = $job.Name.Replace("OllamaDownload_", "").Replace("_", ":")
            Write-Host "  Job $($job.Id): $modelName - $($job.State)" -ForegroundColor Gray
            
            if ($job.State -eq "Completed") {
                $result = Receive-Job -Job $job
                if ($result.Success) {
                    Write-Host "    ✅ Download completed successfully" -ForegroundColor Green
                }
                else {
                    Write-Host "    ❌ Download failed: $($result.Output)" -ForegroundColor Red
                }
                Remove-Job -Job $job
            }
            elseif ($job.State -eq "Failed") {
                Write-Host "    ❌ Job failed" -ForegroundColor Red
                Remove-Job -Job $job
            }
        }
    }
    else {
        Write-Host "  No active download jobs" -ForegroundColor Gray
    }
}

# Main execution
switch ($Action) {
    "status" {
        Show-ModelStatus
        Show-DownloadJobs
    }
    
    "resume" {
        if ($Model) {
            Resume-ModelDownload -ModelName $Model
        }
        else {
            # Resume all models that need it
            foreach ($modelConfig in $RequiredModels) {
                $status = Get-ModelStatus -ModelName $modelConfig.Name
                if ($status.Status -eq "Downloading" -or ($status.ManifestExists -and -not $status.Listed)) {
                    Write-Host "🔄 Resuming $($modelConfig.Name)..." -ForegroundColor Cyan
                    Resume-ModelDownload -ModelName $modelConfig.Name
                    Start-Sleep -Seconds 2  # Brief pause between downloads
                }
            }
        }
        
        Write-Host ""
        Write-Host "💡 Tip: Use 'Get-Job' to monitor background downloads" -ForegroundColor Yellow
        Write-Host "💡 Tip: Run this script with -Action status to check progress" -ForegroundColor Yellow
    }
    
    "download" {
        if ($Model) {
            Resume-ModelDownload -ModelName $Model
        }
        else {
            Write-Host "❌ Please specify a model name with -Model parameter" -ForegroundColor Red
            $modelNames = $RequiredModels | ForEach-Object { $_.Name }
            Write-Host "Available models: $($modelNames -join ', ')" -ForegroundColor Gray
        }
    }
    
    "test" {
        Test-Models
    }
    
    "cleanup" {
        Cleanup-PartialDownloads
    }
}

Write-Host ""
Write-Host "🏁 Model Manager Complete" -ForegroundColor Green