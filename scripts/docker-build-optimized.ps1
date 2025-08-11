# Script optimizado para builds de Docker con cache
param(
    [string]$Service = "",
    [switch]$NoCache = $false,
    [switch]$Parallel = $false,
    [switch]$Verbose = $false
)

Write-Host "=== Docker Build Optimizado ===" -ForegroundColor Green

# Función para verificar si Docker BuildKit está habilitado
function Test-BuildKitEnabled {
    # First check environment variable
    if ($env:DOCKER_BUILDKIT -eq "1" -or $env:DOCKER_BUILDKIT -eq "true") {
        return $true
    }
    
    # Then check for buildx availability
    try {
        $null = docker buildx version 2>$null
        return $LASTEXITCODE -eq 0
    }
    catch {
        return $false
    }
}

# Función para habilitar BuildKit si no está activo
function Enable-BuildKit {
    if (-not (Test-BuildKitEnabled)) {
        Write-Host "Habilitando Docker BuildKit para mejor rendimiento..." -ForegroundColor Yellow
        $env:DOCKER_BUILDKIT = "1"
        $env:COMPOSE_DOCKER_CLI_BUILD = "1"
    } else {
        Write-Host "Docker BuildKit ya está habilitado" -ForegroundColor Green
    }
}

# Función para construir un servicio específico
function Build-Service {
    param(
        [string]$ServiceName,
        [bool]$UseCache = $true
    )
    
    Write-Host "`n--- Construyendo $ServiceName ---" -ForegroundColor Yellow
    
    $buildArgs = @("build")
    
    if (-not $UseCache) {
        $buildArgs += "--no-cache"
    }
    
    if ($Verbose) {
        $buildArgs += "--progress=plain"
    }
    
    $buildArgs += $ServiceName
    
    try {
        $startTime = Get-Date
        & docker-compose @buildArgs
        $endTime = Get-Date
        $duration = $endTime - $startTime
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "OK $ServiceName construido exitosamente en $($duration.TotalSeconds.ToString('F1'))s" -ForegroundColor Green
            return $true
        } else {
            Write-Host "ERROR construyendo $ServiceName" -ForegroundColor Red
            return $false
        }
    }
    catch {
        Write-Host "ERROR construyendo $ServiceName`: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Función para construir servicios en paralelo
function Build-ServicesParallel {
    param([string[]]$Services)
    
    Write-Host "Construyendo servicios en paralelo..." -ForegroundColor Yellow
    
    # Create logs directory if it doesn't exist
    $logsDir = "logs"
    if (-not (Test-Path $logsDir)) {
        New-Item -ItemType Directory -Path $logsDir -Force | Out-Null
    }
    
    $jobs = @()
    foreach ($service in $Services) {
        $job = Start-Job -ScriptBlock {
            param($serviceName, $useCache, $verbose, $logDir)
            
            $env:DOCKER_BUILDKIT = "1"
            $env:COMPOSE_DOCKER_CLI_BUILD = "1"
            
            # Create unique log file for this service
            $timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
            $logFile = Join-Path $logDir "build-$serviceName-$timestamp.log"
            
            $buildArgs = @("build")
            if (-not $useCache) { $buildArgs += "--no-cache" }
            if ($verbose) { $buildArgs += "--progress=plain" }
            $buildArgs += $serviceName
            
            try {
                # Redirect all output to log file
                & docker-compose @buildArgs > $logFile 2>&1
                $exitCode = $LASTEXITCODE
            }
            catch {
                $exitCode = 1
                "Error: $($_.Exception.Message)" | Out-File -FilePath $logFile -Append
            }
            
            # Return structured result as PSCustomObject
            return [PSCustomObject]@{
                Service = $serviceName
                ExitCode = $exitCode
                LogFile = $logFile
            }
        } -ArgumentList $service, (-not $NoCache), $Verbose, $logsDir
        
        $jobs += @{Job = $job; Service = $service}
    }
    
    # Esperar a que terminen todos los jobs
    $results = @()
    foreach ($jobInfo in $jobs) {
        $result = Receive-Job -Job $jobInfo.Job -Wait
        Remove-Job -Job $jobInfo.Job
        
        # Display log file content only if build failed
        if ($result.ExitCode -ne 0) {
            Write-Host "`nERROR Build failed for $($result.Service). Log output:" -ForegroundColor Red
            Write-Host "----------------------------------------" -ForegroundColor Gray
            if (Test-Path $result.LogFile) {
                Get-Content $result.LogFile | Write-Host -ForegroundColor Gray
            }
            Write-Host "----------------------------------------" -ForegroundColor Gray
        }
        
        $results += @{
            Service = $result.Service
            Success = ($result.ExitCode -eq 0)
            LogFile = $result.LogFile
        }
    }
    
    return $results
}

# Función para limpiar cache de Docker
function Clear-DockerCache {
    Write-Host "`n--- Limpiando cache de Docker ---" -ForegroundColor Yellow
    
    try {
        Write-Host "Eliminando imágenes no utilizadas..." -ForegroundColor Cyan
        docker image prune -f
        
        Write-Host "Eliminando cache de build..." -ForegroundColor Cyan
        docker builder prune -f
        
        Write-Host "Cache limpiado exitosamente" -ForegroundColor Green
    }
    catch {
        Write-Host "ERROR limpiando cache: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Habilitar BuildKit
Enable-BuildKit

# Lista de servicios disponibles
$availableServices = @("auth-service", "creator-hub-service", "ai-engine-service", "channel-service")

# Determinar qué servicios construir
$servicesToBuild = @()
if ($Service -and $Service -ne "") {
    if ($availableServices -contains $Service) {
        $servicesToBuild = @($Service)
    } else {
        Write-Host "ERROR Servicio '$Service' no encontrado. Servicios disponibles: $($availableServices -join ', ')" -ForegroundColor Red
        exit 1
    }
} else {
    $servicesToBuild = $availableServices
}

Write-Host "Servicios a construir: $($servicesToBuild -join ', ')" -ForegroundColor Cyan

# Mostrar información de cache
if ($NoCache) {
    Write-Host "WARNING Construyendo sin cache (--no-cache)" -ForegroundColor Yellow
} else {
    Write-Host "INFO Usando cache de Docker para acelerar builds" -ForegroundColor Green
}

# Construir servicios
$buildResults = @()
$totalStartTime = Get-Date

if ($Parallel -and $servicesToBuild.Count -gt 1) {
    Write-Host "`n🚀 Modo paralelo activado" -ForegroundColor Green
    $buildResults = Build-ServicesParallel -Services $servicesToBuild
} else {
    foreach ($service in $servicesToBuild) {
        $success = Build-Service -ServiceName $service -UseCache (-not $NoCache)
        $buildResults += @{Service = $service; Success = $success}
    }
}

$totalEndTime = Get-Date
$totalDuration = $totalEndTime - $totalStartTime

# Mostrar resumen
Write-Host "`n=== RESUMEN DE BUILD ===" -ForegroundColor Green
$successCount = 0
foreach ($result in $buildResults) {
    $status = if ($result.Success) { "OK" } else { "ERROR" }
    Write-Host "  $status $($result.Service)" -ForegroundColor $(if ($result.Success) { "Green" } else { "Red" })
    if ($result.Success) { $successCount++ }
}

Write-Host "`nTiempo total: $($totalDuration.TotalSeconds.ToString('F1'))s" -ForegroundColor Cyan
Write-Host "Resultado: $successCount/$($buildResults.Count) servicios construidos exitosamente" -ForegroundColor $(if ($successCount -eq $buildResults.Count) { "Green" } else { "Yellow" })

# Sugerir limpieza si hay errores
if ($successCount -lt $buildResults.Count) {
    Write-Host "`nSugerencia: Si hay errores persistentes, intenta:" -ForegroundColor Yellow
    Write-Host "   .\scripts\docker-build-optimized.ps1 -NoCache" -ForegroundColor Gray
    Write-Host "   o ejecuta Clear-DockerCache para limpiar el cache" -ForegroundColor Gray
}

# Mostrar comandos útiles
Write-Host "`nComandos utiles:" -ForegroundColor Cyan
Write-Host "   docker-compose up -d                    # Iniciar servicios" -ForegroundColor Gray
Write-Host "   docker-compose logs -f <service>        # Ver logs" -ForegroundColor Gray
Write-Host "   .\scripts\test-api-gateway.ps1          # Probar API Gateway" -ForegroundColor Gray

if ($successCount -eq $buildResults.Count) {
    Write-Host "`nTodos los servicios construidos exitosamente!" -ForegroundColor Green
    exit 0
} else {
    exit 1
}