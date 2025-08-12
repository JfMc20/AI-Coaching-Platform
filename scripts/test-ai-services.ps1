#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test AI services (ChromaDB and Ollama) connectivity and functionality
.DESCRIPTION
    This script tests the AI Engine service endpoints for ChromaDB and Ollama integration
.PARAMETER BaseUrl
    Base URL for the AI Engine service (default: http://localhost:8003)
.PARAMETER TimeoutSec
    Timeout in seconds for HTTP requests (default: 30)
#>

param(
    [string]$BaseUrl = "http://localhost:8003",
    [int]$TimeoutSec = 30
)

Write-Host "🧪 Testing AI Services Integration" -ForegroundColor Cyan
Write-Host "Base URL: $BaseUrl" -ForegroundColor Gray
Write-Host "Timeout: ${TimeoutSec}s" -ForegroundColor Gray
Write-Host ""

# Test results tracking
$TestResults = @()

function Test-Endpoint {
    param(
        [string]$Name,
        [string]$Url,
        [string]$Method = "GET",
        [hashtable]$Body = $null,
        [int]$ExpectedStatus = 200
    )
    
    Write-Host "Testing $Name..." -NoNewline
    
    try {
        $params = @{
            Uri = $Url
            Method = $Method
            TimeoutSec = $TimeoutSec
            ErrorAction = 'Stop'
        }
        
        if ($Body) {
            $params.Body = ($Body | ConvertTo-Json)
            $params.ContentType = "application/json"
        }
        
        $response = Invoke-WebRequest @params
        
        if ($response.StatusCode -eq $ExpectedStatus) {
            Write-Host " ✅ PASS" -ForegroundColor Green
            $script:TestResults += @{
                Name = $Name
                Status = "PASS"
                StatusCode = $response.StatusCode
                Response = $response.Content | ConvertFrom-Json -ErrorAction SilentlyContinue
            }
        } else {
            Write-Host " ❌ FAIL (Status: $($response.StatusCode))" -ForegroundColor Red
            $script:TestResults += @{
                Name = $Name
                Status = "FAIL"
                StatusCode = $response.StatusCode
                Error = "Unexpected status code"
            }
        }
    }
    catch {
        Write-Host " ❌ FAIL" -ForegroundColor Red
        Write-Host "   Error: $($_.Exception.Message)" -ForegroundColor Red
        $script:TestResults += @{
            Name = $Name
            Status = "FAIL"
            Error = $_.Exception.Message
        }
    }
}

# Test basic health endpoints
Write-Host "🏥 Health Checks" -ForegroundColor Yellow
Test-Endpoint "AI Engine Health" "$BaseUrl/health"
Test-Endpoint "AI Engine Readiness" "$BaseUrl/ready"

Write-Host ""

# Test ChromaDB integration
Write-Host "🗄️ ChromaDB Integration" -ForegroundColor Yellow
Test-Endpoint "ChromaDB Health" "$BaseUrl/api/v1/ai/chromadb/health"
Test-Endpoint "ChromaDB Stats" "$BaseUrl/api/v1/ai/chromadb/stats"

Write-Host ""

# Test Ollama integration
Write-Host "🤖 Ollama Integration" -ForegroundColor Yellow
Test-Endpoint "Ollama Health" "$BaseUrl/api/v1/ai/ollama/health"
Test-Endpoint "Models Status" "$BaseUrl/api/v1/ai/models/status"

Write-Host ""

# Test Ollama functionality (if models are available)
Write-Host "🧠 AI Functionality Tests" -ForegroundColor Yellow
Test-Endpoint "Test Embedding Generation" "$BaseUrl/api/v1/ai/ollama/test-embedding" "POST"
Test-Endpoint "Test Chat Generation" "$BaseUrl/api/v1/ai/ollama/test-chat" "POST"

Write-Host ""

# Summary
Write-Host "📊 Test Summary" -ForegroundColor Cyan
$PassCount = ($TestResults | Where-Object { $_.Status -eq "PASS" }).Count
$FailCount = ($TestResults | Where-Object { $_.Status -eq "FAIL" }).Count
$TotalCount = $TestResults.Count

Write-Host "Total Tests: $TotalCount" -ForegroundColor Gray
Write-Host "Passed: $PassCount" -ForegroundColor Green
Write-Host "Failed: $FailCount" -ForegroundColor Red

if ($FailCount -gt 0) {
    Write-Host ""
    Write-Host "❌ Failed Tests:" -ForegroundColor Red
    $TestResults | Where-Object { $_.Status -eq "FAIL" } | ForEach-Object {
        Write-Host "  - $($_.Name): $($_.Error)" -ForegroundColor Red
    }
}

Write-Host ""

# Show detailed results for successful tests
$SuccessfulTests = $TestResults | Where-Object { $_.Status -eq "PASS" -and $_.Response }
if ($SuccessfulTests.Count -gt 0) {
    Write-Host "✅ Successful Test Details:" -ForegroundColor Green
    foreach ($test in $SuccessfulTests) {
        Write-Host "  $($test.Name):" -ForegroundColor Cyan
        if ($test.Response) {
            $test.Response | ConvertTo-Json -Depth 3 | Write-Host -ForegroundColor Gray
        }
        Write-Host ""
    }
}

# Exit with appropriate code
if ($FailCount -gt 0) {
    exit 1
} else {
    Write-Host "🎉 All tests passed!" -ForegroundColor Green
    exit 0
}