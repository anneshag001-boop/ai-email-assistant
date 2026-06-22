param(
    [int]$Port = 8000,
    [string]$BindAddr = "0.0.0.0",
    [switch]$Reload = $false,
    [switch]$Stop = $false
)

$ProjectDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$VenvPython = Join-Path $ProjectDir ".venv\Scripts\python.exe"
$PidFile = Join-Path $ProjectDir "server.pid"

function Start-Server {
    if (Test-Path $PidFile) {
        $oldPid = Get-Content $PidFile
        $proc = Get-Process -Id $oldPid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Server already running (PID $oldPid) on http://$BindAddr`:$Port" -ForegroundColor Yellow
            return
        }
        Remove-Item $PidFile -Force
    }

    if (-not (Test-Path $VenvPython)) {
        Write-Host "ERROR: .venv not found. Run 'python -m venv .venv' first." -ForegroundColor Red
        exit 1
    }

    $reloadArg = if ($Reload) { "--reload" } else { "" }
    $logFile = Join-Path $ProjectDir "server.log"

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $VenvPython
    $psi.Arguments = "-m uvicorn app.main:app --host $BindAddr --port $Port $reloadArg"
    $psi.WorkingDirectory = $ProjectDir
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.UseShellExecute = $false
    $psi.CreateNoWindow = $true

    $process = [System.Diagnostics.Process]::Start($psi)
    Start-Sleep -Seconds 3

    if ($process.HasExited) {
        $stderr = $process.StandardError.ReadToEnd()
        Write-Host "Server failed to start:" -ForegroundColor Red
        Write-Host $stderr -ForegroundColor Red
        exit 1
    }

    $process.Id | Out-File -FilePath $PidFile -Force

    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()

    Write-Host "Server started (PID $($process.Id))" -ForegroundColor Green
    Write-Host "  URL:       http://$BindAddr`:$Port" -ForegroundColor Cyan
    Write-Host "  Docs:      http://$BindAddr`:$Port/docs" -ForegroundColor Cyan
    Write-Host "  Login:     http://$BindAddr`:$Port/auth/login" -ForegroundColor Cyan
    Write-Host "  Log file:  $logFile" -ForegroundColor Gray

    # Start logging background job
    Start-Job -ScriptBlock {
        param($pid, $logFile, $stdoutTask, $stderrTask)
        $stdout = $stdoutTask.Result
        $stderr = $stderrTask.Result
        $output = if ($stdout) { $stdout } else { "" }
        if ($stderr) { $output += "`n$stderr" }
        $output | Out-File -FilePath $logFile -Append -Encoding UTF8
    } -ArgumentList $process.Id, $logFile, $stdoutTask, $stderrTask | Out-Null
}

function Stop-Server {
    if (-not (Test-Path $PidFile)) {
        Write-Host "No running server found." -ForegroundColor Yellow
        return
    }
    $pid = Get-Content $PidFile
    $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
    if ($proc) {
        Stop-Process -Id $pid -Force
        Write-Host "Server (PID $pid) stopped." -ForegroundColor Green
    } else {
        Write-Host "Server (PID $pid) already exited." -ForegroundColor Yellow
    }
    Remove-Item $PidFile -Force
}

function Status-Server {
    if (Test-Path $PidFile) {
        $pid = Get-Content $PidFile
        $proc = Get-Process -Id $pid -ErrorAction SilentlyContinue
        if ($proc) {
            Write-Host "Server running (PID $pid) on http://$BindAddr`:$Port" -ForegroundColor Green
        } else {
            Write-Host "Stale PID file (PID $pid no longer running)" -ForegroundColor Yellow
            Remove-Item $PidFile -Force
        }
    } else {
        Write-Host "Server not running." -ForegroundColor Yellow
    }
}

# Main
if ($Stop) {
    Stop-Server
} elseif ($MyInvocation.ExpectingInput -eq $false -and $args.Count -eq 0 -and $Reload -eq $false -and $Stop -eq $false) {
    # No args -> start
    Start-Server
} else {
    Start-Server
}
