# Script para probar las dependencias de servicios
param(
    [string]$Service = "",
    [int]$TimeoutSec = 300,
    [switch]$Verbose = $false
)

Write-Host "=== Probando Dependencias de Servicios ===" -ForegroundColor Green

# Función para probar dependencias TCP
function Test-TcpDependency {
    param(
        [string]$HostName,
        [int]$Port,
        [int]$TimeoutSec = 5
    )
    
    try {
        $tcpClient = New-Object System.Net.Sockets.TcpClient
        $asyncResult = $tcpClient.BeginConnect($HostName, $Port, $null, $null)
        $wait = $asyncResult.AsyncWaitHandle.WaitOne($TimeoutSec * 1000, $false)
        
        if ($wait) {
            $tcpClient.EndConnect($asyncResult)
            $tcpClient.Close()
            return $true
        } else {
            $tcpClient.Close()
            return $false
        }
    }
    catch {
        return $false
    }
}

# Función para probar dependencias HTTP
function Test-HttpDependency {
    param(
        [string]$Url,
        [int]$TimeoutSec = 10
    )
    
    try {
        $response = Invoke-WebRequest -Uri $Url -Method GET -TimeoutSec $TimeoutSec -ErrorAction Stop
        return ($response.StatusCode -ge 200 -and $response.StatusCode -le 299)
    }
    catch {
        return $false
    }
}

# Definir dependencias por servicio
$serviceDependencies = @{
    "auth-service" = @(
        @{Type="TCP"; Host="localhost"; Port=5432; Name="PostgreSQL"},
        @{Type="TCP"; Host="localhost"; Port=6379; Name="Redis"}
    )
    "creator-hub-service" = @(
        @{Type="TCP"; Host="localhost"; Port=5432; Name="PostgreSQL"},
        @{Type="TCP"; Host="localhost"; Port=6379; Name="Redis"},
        @{Type="HTTP"; Url="http://localhost:8001/health"; Name="Auth Service"}
    )
    "ai-engine-service" = @(
        @{Type="TCP"; Host="localhost"; Port=5432; Name="PostgreSQL"},
        @{Type="TCP"; Host="localhost"; Port=6379; Name="Redis"},
        @{Type="TCP"; Host="localhost"; Port=11434; Name="Ollama"},
        @{Type="TCP"; Host="localhost"; Port=8000; Name="ChromaDB"}
    )
    "channel-service" = @(
        @{Type="TCP"; Host="localhost"; Port=5432; Name="PostgreSQL"},
        @{Type="TCP"; Host="localhost"; Port=6379; Name="Redis"},
        @{Type="HTTP"; Url="http://localhost:8001/health"; Name="Auth Service"},
        @{Type="HTTP"; Url="http://localhost:8003/health"; Name="AI Engine Service"}
    )
}

# Función para probar dependencias de un servicio
function Test-ServiceDependencies {
    param(
        [string]$ServiceName,
        [array]$Dependencies
    )
    
    Write-Host "`n--- Probando dependencias de $ServiceName ---" -ForegroundColor Yellow
    
    $allHealthy = $true
    foreach ($dep in $Dependencies) {
        $isHealthy = $false
        
        if ($dep.Type -eq "TCP") {
            $isHealthy = Test-TcpDependency -HostName $dep.Host -Port $dep.Port -TimeoutSec 5
            $target = "$($dep.Host):$($dep.Port)"
        } elseif ($dep.Type -eq "HTTP") {
            $isHealthy = Test-HttpDependency -Url $dep.Url -TimeoutSec 10
            $target = $dep.Url
        }
        
        if ($isHealthy) {
            Write-Host "  OK $($dep.Name) ($target)" -ForegroundColor Green
        } else {
            Write-Host "  ERROR $($dep.Name) ($target)" -ForegroundColor Red
            $allHealthy = $false
        }
    }
    
    return $allHealthy
}

# Función para esperar a que las dependencias estén listas
function Wait-ForDependencies {
    param(
        [string]$ServiceName,
        [array]$Dependencies,
        [int]$TimeoutSec
    )
    
    Write-Host "`nEsperando dependencias de $ServiceName (timeout: ${TimeoutSec}s)..." -ForegroundColor Cyan
    
    $startTime = Get-Date
    $interval = 5
    
    $deadline = (Get-Date).AddSeconds($TimeoutSec)
    
    while ((Get-Date) -lt $deadline) {
        if (Test-ServiceDependencies -ServiceName $ServiceName -Dependencies $Dependencies) {
            Write-Host "Todas las dependencias de $ServiceName están listas!" -ForegroundColor Green
            return $true
        }
        
        Write-Host "Reintentando en ${interval}s..." -ForegroundColor Gray
        Start-Sleep -Seconds $interval
    }
    
    Write-Host "Timeout esperando dependencias de $ServiceName" -ForegroundColor Red
    return $false
}

# Probar servicio específico o todos
if ($Service -and $Service -ne "") {
    if ($serviceDependencies.ContainsKey($Service)) {
        $dependencies = $serviceDependencies[$Service]
        
        if (Wait-ForDependencies -ServiceName $Service -Dependencies $dependencies -TimeoutSec $TimeoutSec) {
            Write-Host "`nServicio $Service listo para iniciar!" -ForegroundColor Green
            exit 0
        } else {
            Write-Host "`nServicio $Service NO está listo" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "Servicio '$Service' no encontrado. Servicios disponibles: $($serviceDependencies.Keys -join ', ')" -ForegroundColor Red
        exit 1
    }
} else {
    # Probar todos los servicios
    Write-Host "Probando dependencias de todos los servicios..." -ForegroundColor Cyan
    
    $results = @()
    foreach ($serviceName in $serviceDependencies.Keys) {
        $dependencies = $serviceDependencies[$serviceName]
        $isReady = Test-ServiceDependencies -ServiceName $serviceName -Dependencies $dependencies
        
        $results += @{
            Service = $serviceName
            Ready = $isReady
        }
    }
    
    # Mostrar resumen
    Write-Host "`n=== RESUMEN ===" -ForegroundColor Green
    $readyCount = 0
    foreach ($result in $results) {
        $status = if ($result.Ready) { "READY" } else { "NOT READY" }
        $color = if ($result.Ready) { "Green" } else { "Red" }
        Write-Host "  $status $($result.Service)" -ForegroundColor $color
        if ($result.Ready) { $readyCount++ }
    }
    
    $totalCount = $results.Count
    Write-Host "`nResultado: $readyCount/$totalCount servicios listos" -ForegroundColor $(if ($readyCount -eq $totalCount) { "Green" } else { "Yellow" })
    
    if ($readyCount -eq $totalCount) {
        Write-Host "Todos los servicios están listos para iniciar!" -ForegroundColor Green
        exit 0
    } else {
        exit 1
    }
}