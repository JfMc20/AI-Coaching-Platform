# Script para monitorear salud de servicios Docker
param(
    [int]$IntervalSeconds = 30,
    [switch]$Continuous = $false,
    [switch]$RestartUnhealthy = $false,
    [string]$LogFile = ""
)

Write-Host "=== Monitor de Salud Docker ===" -ForegroundColor Green

# Función para obtener estado de contenedores usando docker inspect
function Get-ContainerHealth {
    try {
        # Get container names from docker-compose
        $containerNames = docker-compose ps -q | ForEach-Object { $_.Trim() } | Where-Object { $_ -ne "" }
        $healthStatus = @()
        
        foreach ($containerName in $containerNames) {
            if ([string]::IsNullOrWhiteSpace($containerName)) { continue }
            
            try {
                # Get container state and health using docker inspect
                $inspectResult = docker inspect $containerName --format '{{.Name}}|{{.Config.Labels}}|{{.State.Status}}|{{.State.Health.Status}}|{{.NetworkSettings.Ports}}' 2>$null
                
                if ($inspectResult) {
                    $parts = $inspectResult -split '\|'
                    $containerFullName = $parts[0] -replace '^/', ''  # Remove leading slash
                    $labels = $parts[1]
                    $state = $parts[2]
                    $health = $parts[3]
                    $ports = $parts[4]
                    
                    # Extract service name from labels or container name
                    $serviceName = ""
                    if ($labels -match 'com\.docker\.compose\.service:([^,}]+)') {
                        $serviceName = $matches[1]
                    } else {
                        # Fallback: extract from container name pattern
                        if ($containerFullName -match 'mvp-(.+)') {
                            $serviceName = $matches[1]
                        } else {
                            $serviceName = $containerFullName
                        }
                    }
                    
                    $status = @{
                        Name = $containerFullName
                        Service = $serviceName
                        State = $state
                        Health = if ([string]::IsNullOrWhiteSpace($health) -or $health -eq "<no value>") { "no-healthcheck" } else { $health }
                        Ports = $ports
                    }
                    
                    $healthStatus += $status
                }
            }
            catch {
                Write-Host "Warning: Could not inspect container $containerName`: $($_.Exception.Message)" -ForegroundColor Yellow
            }
        }
        
        return $healthStatus
    }
    catch {
        Write-Host "Error obteniendo estado de contenedores: $($_.Exception.Message)" -ForegroundColor Red
        return @()
    }
}

# Función para verificar conectividad de servicios
function Test-ServiceConnectivity {
    $services = @(
        @{Name = "Auth Service"; Url = "http://localhost:8001/health"},
        @{Name = "Creator Hub"; Url = "http://localhost:8002/health"},
        @{Name = "AI Engine"; Url = "http://localhost:8003/health"},
        @{Name = "Channel Service"; Url = "http://localhost:8004/health"},
        @{Name = "API Gateway"; Url = "http://localhost/health"}
    )
    
    $connectivity = @()
    foreach ($service in $services) {
        try {
            $response = Invoke-WebRequest -Uri $service.Url -Method GET -TimeoutSec 5 -ErrorAction Stop
            $connectivity += @{
                Name = $service.Name
                Status = "healthy"
                ResponseTime = $response.Headers["X-Response-Time"]
                StatusCode = $response.StatusCode
            }
        }
        catch {
            $connectivity += @{
                Name = $service.Name
                Status = "unhealthy"
                Error = $_.Exception.Message
                StatusCode = $null
            }
        }
    }
    
    return $connectivity
}

# Función para reiniciar servicios no saludables
function Restart-UnhealthyServices {
    param([array]$HealthStatus)
    
    # Use canonical Docker state and health values
    $unhealthyServices = $HealthStatus | Where-Object { 
        $_.Health -eq "unhealthy" -or 
        $_.State -eq "exited" -or 
        $_.State -eq "dead" -or 
        $_.State -eq "restarting"
    }
    
    if ($unhealthyServices.Count -gt 0) {
        Write-Host "`nReiniciando servicios no saludables..." -ForegroundColor Yellow
        
        foreach ($service in $unhealthyServices) {
            try {
                Write-Host "Reiniciando $($service.Service) (Estado: $($service.State), Salud: $($service.Health))..." -ForegroundColor Cyan
                docker-compose restart $service.Service
                Start-Sleep -Seconds 10  # Esperar a que el servicio se inicie
                
                Write-Host "OK $($service.Service) reiniciado" -ForegroundColor Green
            }
            catch {
                Write-Host "ERROR reiniciando $($service.Service): $($_.Exception.Message)" -ForegroundColor Red
            }
        }
    }
}

# Función para log de eventos
function Write-LogEntry {
    param(
        [string]$Message,
        [string]$Level = "INFO"
    )
    
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $logEntry = "[$timestamp] [$Level] $Message"
    
    if ($LogFile -and $LogFile -ne "") {
        Add-Content -Path $LogFile -Value $logEntry
    }
    
    $color = switch ($Level) {
        "ERROR" { "Red" }
        "WARN" { "Yellow" }
        "INFO" { "White" }
        default { "Gray" }
    }
    
    Write-Host $logEntry -ForegroundColor $color
}

# Función principal de monitoreo
function Start-HealthMonitoring {
    do {
        $timestamp = Get-Date -Format "HH:mm:ss"
        Write-Host "`n=== Verificación de Salud - $timestamp ===" -ForegroundColor Cyan
        
        # Obtener estado de contenedores
        $containerHealth = Get-ContainerHealth
        
        if ($containerHealth.Count -eq 0) {
            Write-LogEntry "No se encontraron contenedores en ejecución" "WARN"
            if ($Continuous) {
                Start-Sleep -Seconds $IntervalSeconds
                continue
            } else {
                break
            }
        }
        
        # Mostrar estado de contenedores usando valores canónicos
        Write-Host "`nEstado de Contenedores:" -ForegroundColor Yellow
        foreach ($container in $containerHealth) {
            $healthIcon = switch ($container.Health) {
                "healthy" { "OK" }
                "unhealthy" { "ERROR" }
                "starting" { "STARTING" }
                "no-healthcheck" { "NO-CHECK" }
                default { "UNKNOWN" }
            }
            
            $stateIcon = switch ($container.State) {
                "running" { "RUNNING" }
                "exited" { "EXITED" }
                "paused" { "PAUSED" }
                "dead" { "DEAD" }
                "restarting" { "RESTARTING" }
                default { "UNKNOWN" }
            }
            
            $statusColor = if ($container.State -eq "running" -and ($container.Health -eq "healthy" -or $container.Health -eq "no-healthcheck")) { "Green" } else { "Red" }
            
            Write-Host "  [$healthIcon] [$stateIcon] $($container.Service) ($($container.Name))" -ForegroundColor $statusColor
            if ($container.Ports -and $container.Ports -ne "<no value>") {
                Write-Host "    Puertos: $($container.Ports)" -ForegroundColor Gray
            }
        }
        
        # Verificar conectividad de servicios
        Write-Host "`n🌐 Conectividad de Servicios:" -ForegroundColor Yellow
        $connectivity = Test-ServiceConnectivity
        
        $healthyCount = 0
        foreach ($service in $connectivity) {
            if ($service.Status -eq "healthy") {
                Write-Host "  ✅ $($service.Name) - $($service.StatusCode)" -ForegroundColor Green
                $healthyCount++
            } else {
                Write-Host "  ❌ $($service.Name) - $($service.Error)" -ForegroundColor Red
                Write-LogEntry "$($service.Name) no saludable: $($service.Error)" "ERROR"
            }
        }
        
        # Resumen
        $totalServices = $connectivity.Count
        Write-Host "`n📊 Resumen: $healthyCount/$totalServices servicios saludables" -ForegroundColor $(if ($healthyCount -eq $totalServices) { "Green" } else { "Yellow" })
        
        # Reiniciar servicios no saludables si está habilitado
        if ($RestartUnhealthy) {
            Restart-UnhealthyServices -HealthStatus $containerHealth
        }
        
        # Log del estado general
        if ($healthyCount -eq $totalServices) {
            Write-LogEntry "Todos los servicios están saludables ($healthyCount/$totalServices)" "INFO"
        } else {
            Write-LogEntry "Servicios con problemas detectados ($healthyCount/$totalServices saludables)" "WARN"
        }
        
        if ($Continuous) {
            Write-Host "`n⏱️  Próxima verificación en $IntervalSeconds segundos..." -ForegroundColor Gray
            Write-Host "Presiona Ctrl+C para detener el monitoreo" -ForegroundColor Gray
            Start-Sleep -Seconds $IntervalSeconds
        }
        
    } while ($Continuous)
}

# Mostrar configuración
Write-Host "Configuración del monitor:" -ForegroundColor Cyan
Write-Host "  Intervalo: $IntervalSeconds segundos" -ForegroundColor Gray
Write-Host "  Continuo: $Continuous" -ForegroundColor Gray
Write-Host "  Reinicio automático: $RestartUnhealthy" -ForegroundColor Gray
if ($LogFile) {
    Write-Host "  Archivo de log: $LogFile" -ForegroundColor Gray
}

# Iniciar monitoreo
try {
    Start-HealthMonitoring
}
catch {
    Write-LogEntry "Error en el monitoreo: $($_.Exception.Message)" "ERROR"
    exit 1
}

Write-Host "`n✅ Monitoreo completado" -ForegroundColor Green