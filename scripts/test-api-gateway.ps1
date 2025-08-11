# Script para probar el API Gateway
param(
    [string]$BaseUrl = "http://localhost",
    [int]$TimeoutSec = 10,
    [switch]$Verbose = $false,
    [int]$MaxContentLength = 200,
    [string]$Environment = "development"
)

Write-Host "=== Probando API Gateway ===" -ForegroundColor Green
Write-Host "Configuracion:" -ForegroundColor Cyan
Write-Host "  Base URL: $BaseUrl" -ForegroundColor Gray
Write-Host "  Timeout: $TimeoutSec segundos" -ForegroundColor Gray
Write-Host "  Entorno: $Environment" -ForegroundColor Gray
Write-Host "  Verbose: $Verbose" -ForegroundColor Gray

# Función para detectar si el contenido es JSON
function Test-IsJson {
    param([string]$Content)
    
    if ([string]::IsNullOrWhiteSpace($Content)) {
        return $false
    }
    
    try {
        $null = $Content | ConvertFrom-Json
        return $true
    }
    catch {
        return $false
    }
}

# Función para hacer peticiones HTTP y mostrar resultados
function Test-Endpoint {
    param(
        [string]$Url,
        [string]$Description
    )
    
    Write-Host "`n--- $Description ---" -ForegroundColor Yellow
    Write-Host "URL: $Url" -ForegroundColor Cyan
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $TimeoutSec
        Write-Host "OK Status: $($response.StatusCode)" -ForegroundColor Green
        
        # Detectar tipo de contenido de manera robusta
        $isJson = $false
        
        # Verificar Content-Type header
        if ($response.Headers.ContainsKey('Content-Type')) {
            $contentType = $response.Headers['Content-Type']
            if ($contentType -like "*application/json*" -or $contentType -like "*text/json*") {
                $isJson = $true
            }
        }
        
        # Si no hay header o no es JSON, usar heurística
        if (-not $isJson) {
            $isJson = Test-IsJson $response.Content
        }
        
        # Mostrar contenido
        if ($isJson) {
            try {
                $jsonObject = $response.Content | ConvertFrom-Json
                $content = $jsonObject | ConvertTo-Json -Compress
                
                # Truncar contenido si es muy largo y no está en modo verbose
                if (-not $Verbose -and $content.Length -gt $MaxContentLength) {
                    $truncated = $content.Substring(0, $MaxContentLength) + "..."
                    Write-Host "Response: $truncated" -ForegroundColor White
                } else {
                    Write-Host "Response: $content" -ForegroundColor White
                }
            }
            catch {
                Write-Host "Response: [Invalid JSON - $($response.Content.Length) bytes]" -ForegroundColor Yellow
            }
        } else {
            $contentLength = $response.Content.Length
            Write-Host "Content-Length: $contentLength bytes" -ForegroundColor White
            
            # Mostrar preview del contenido si es texto y está en modo verbose
            if ($Verbose -and $contentLength -gt 0 -and $contentLength -lt 1000) {
                $preview = $response.Content.Substring(0, [Math]::Min(200, $contentLength))
                Write-Host "Preview: $preview..." -ForegroundColor Gray
            }
        }
        
        return $true
    }
    catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Probar health check de Nginx
Test-Endpoint "$BaseUrl/health" "Nginx Health Check"

# Probar health checks de servicios
$services = @(
    @{Name="Auth Service"; Url="$BaseUrl/api/v1/auth/health"},
    @{Name="Creator Hub Service"; Url="$BaseUrl/api/v1/creators/health"},
    @{Name="AI Engine Service"; Url="$BaseUrl/api/v1/ai/health"},
    @{Name="Channel Service"; Url="$BaseUrl/api/v1/channels/health"}
)

$healthResults = @()
foreach ($service in $services) {
    $result = Test-Endpoint $service.Url "$($service.Name) Health Check"
    $healthResults += @{Name=$service.Name; Success=$result}
}

# Probar documentación de servicios
Write-Host "`n=== Probando Documentación de Servicios ===" -ForegroundColor Green

$docServices = @(
    @{Name="Auth Service Docs"; Url="$BaseUrl/api/v1/auth/docs"},
    @{Name="Creator Hub Docs"; Url="$BaseUrl/api/v1/creators/docs"},
    @{Name="AI Engine Docs"; Url="$BaseUrl/api/v1/ai/docs"},
    @{Name="Channel Service Docs"; Url="$BaseUrl/api/v1/channels/docs"}
)

foreach ($service in $docServices) {
    Test-Endpoint $service.Url $service.Name
}

# Resumen final
Write-Host "`n=== RESUMEN ===" -ForegroundColor Green
Write-Host "Health Checks:" -ForegroundColor Yellow
foreach ($result in $healthResults) {
    $status = if ($result.Success) { "OK" } else { "FAIL" }
    Write-Host "  $status $($result.Name)" -ForegroundColor $(if ($result.Success) { "Green" } else { "Red" })
}

$successCount = ($healthResults | Where-Object { $_.Success }).Count
$totalCount = $healthResults.Count

Write-Host "`nResultado: $successCount/$totalCount servicios funcionando correctamente" -ForegroundColor $(if ($successCount -eq $totalCount) { "Green" } else { "Yellow" })

if ($successCount -eq $totalCount) {
    Write-Host "API Gateway configurado correctamente!" -ForegroundColor Green
} else {
    Write-Host "Algunos servicios necesitan atencion" -ForegroundColor Yellow
}