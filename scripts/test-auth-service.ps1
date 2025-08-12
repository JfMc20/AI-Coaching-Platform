#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Test the Authentication Service endpoints

.DESCRIPTION
    This script tests all the Authentication Service endpoints to ensure they are
    working correctly. It performs basic health checks and API endpoint validation.

.EXAMPLE
    .\scripts\test-auth-service.ps1
    
.EXAMPLE
    .\scripts\test-auth-service.ps1 -BaseUrl "http://localhost:8001"
#>

param(
    [string]$BaseUrl = "http://localhost:8001",
    [int]$TimeoutSeconds = 30
)

Write-Host "Testing Authentication Service at $BaseUrl" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Gray

# Test data
$TestEmail = "test@example.com"
$TestPassword = "TestPassword123!"
$TestName = "Test User"

# Function to make HTTP requests
function Invoke-ApiRequest {
    param(
        [string]$Method,
        [string]$Endpoint,
        [hashtable]$Body = $null,
        [hashtable]$Headers = @{"Content-Type" = "application/json"}
    )
    
    $Uri = "$BaseUrl$Endpoint"
    $RequestParams = @{
        Uri = $Uri
        Method = $Method
        Headers = $Headers
        TimeoutSec = $TimeoutSeconds
    }
    
    if ($Body) {
        $RequestParams.Body = ($Body | ConvertTo-Json -Depth 10)
    }
    
    try {
        $Response = Invoke-RestMethod @RequestParams
        return @{
            Success = $true
            Data = $Response
            StatusCode = 200
        }
    } catch {
        $StatusCode = if ($_.Exception.Response) { 
            [int]$_.Exception.Response.StatusCode 
        } else { 
            0 
        }
        
        return @{
            Success = $false
            Error = $_.Exception.Message
            StatusCode = $StatusCode
        }
    }
}

# Function to display test results
function Show-TestResult {
    param(
        [string]$TestName,
        [hashtable]$Result,
        [int[]]$ExpectedStatusCodes = @(200)
    )
    
    $Success = $Result.Success -and ($Result.StatusCode -in $ExpectedStatusCodes)
    $Status = if ($Success) { "✅ PASS" } else { "❌ FAIL" }
    $Color = if ($Success) { "Green" } else { "Red" }
    
    Write-Host "$Status $TestName" -ForegroundColor $Color
    
    if (-not $Success) {
        Write-Host "  Error: $($Result.Error)" -ForegroundColor Red
        Write-Host "  Status Code: $($Result.StatusCode)" -ForegroundColor Red
    }
    
    return $Success
}

# Start testing
$AllTestsPassed = $true

Write-Host "1. Health Check Tests" -ForegroundColor Cyan
Write-Host "-" * 30 -ForegroundColor Gray

# Test basic health endpoint
$Result = Invoke-ApiRequest -Method "GET" -Endpoint "/health"
$TestPassed = Show-TestResult -TestName "Basic Health Check" -Result $Result
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Test readiness endpoint
$Result = Invoke-ApiRequest -Method "GET" -Endpoint "/ready"
$TestPassed = Show-TestResult -TestName "Readiness Check" -Result $Result -ExpectedStatusCodes @(200, 503)
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Test root endpoint
$Result = Invoke-ApiRequest -Method "GET" -Endpoint "/"
$TestPassed = Show-TestResult -TestName "Root Endpoint" -Result $Result
$AllTestsPassed = $AllTestsPassed -and $TestPassed

Write-Host ""
Write-Host "2. Authentication Endpoint Tests" -ForegroundColor Cyan
Write-Host "-" * 30 -ForegroundColor Gray

# Test password validation endpoint
$PasswordTestBody = @{
    password = $TestPassword
    personal_info = @{
        email = $TestEmail
        name = $TestName
    }
}
$Result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/v1/auth/password/validate" -Body $PasswordTestBody
$TestPassed = Show-TestResult -TestName "Password Validation" -Result $Result
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Test registration endpoint (should work)
$RegistrationBody = @{
    email = $TestEmail
    password = $TestPassword
    full_name = $TestName
    company_name = "Test Company"
}
$Result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/v1/auth/register" -Body $RegistrationBody
$TestPassed = Show-TestResult -TestName "User Registration" -Result $Result -ExpectedStatusCodes @(201, 409)
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Store tokens if registration was successful
$AccessToken = $null
if ($Result.Success -and $Result.Data.tokens) {
    $AccessToken = $Result.Data.tokens.access_token
    Write-Host "  Access token obtained for further tests" -ForegroundColor Gray
}

# Test login endpoint
$LoginBody = @{
    email = $TestEmail
    password = $TestPassword
    remember_me = $false
}
$Result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/v1/auth/login" -Body $LoginBody
$TestPassed = Show-TestResult -TestName "User Login" -Result $Result -ExpectedStatusCodes @(200, 401)
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Update access token if login was successful
if ($Result.Success -and $Result.Data.tokens) {
    $AccessToken = $Result.Data.tokens.access_token
}

# Test protected endpoints if we have a token
if ($AccessToken) {
    Write-Host ""
    Write-Host "3. Protected Endpoint Tests" -ForegroundColor Cyan
    Write-Host "-" * 30 -ForegroundColor Gray
    
    $AuthHeaders = @{
        "Content-Type" = "application/json"
        "Authorization" = "Bearer $AccessToken"
    }
    
    # Test get current user
    $Result = Invoke-ApiRequest -Method "GET" -Endpoint "/api/v1/auth/me" -Headers $AuthHeaders
    $TestPassed = Show-TestResult -TestName "Get Current User" -Result $Result
    $AllTestsPassed = $AllTestsPassed -and $TestPassed
    
    # Test logout
    $LogoutBody = @{
        refresh_token = "dummy-refresh-token"
    }
    $Result = Invoke-ApiRequest -Method "POST" -Endpoint "/api/v1/auth/logout" -Body $LogoutBody -Headers $AuthHeaders
    $TestPassed = Show-TestResult -TestName "User Logout" -Result $Result -ExpectedStatusCodes @(204)
    $AllTestsPassed = $AllTestsPassed -and $TestPassed
} else {
    Write-Host ""
    Write-Host "⚠️  Skipping protected endpoint tests (no access token)" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "4. Error Handling Tests" -ForegroundColor Cyan
Write-Host "-" * 30 -ForegroundColor Gray

# Test invalid endpoint
$Result = Invoke-ApiRequest -Method "GET" -Endpoint "/api/v1/auth/nonexistent"
$TestPassed = Show-TestResult -TestName "Invalid Endpoint (404)" -Result $Result -ExpectedStatusCodes @(404)
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Test invalid JSON
$InvalidHeaders = @{"Content-Type" = "application/json"}
try {
    $Response = Invoke-RestMethod -Uri "$BaseUrl/api/v1/auth/register" -Method "POST" -Headers $InvalidHeaders -Body "invalid json" -TimeoutSec $TimeoutSeconds
    $TestPassed = $false
} catch {
    $TestPassed = $true
}
$Status = if ($TestPassed) { "✅ PASS" } else { "❌ FAIL" }
$Color = if ($TestPassed) { "Green" } else { "Red" }
Write-Host "$Status Invalid JSON Handling" -ForegroundColor $Color
$AllTestsPassed = $AllTestsPassed -and $TestPassed

# Summary
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Gray
if ($AllTestsPassed) {
    Write-Host "🎉 All tests passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "❌ Some tests failed. Check the output above for details." -ForegroundColor Red
    exit 1
}