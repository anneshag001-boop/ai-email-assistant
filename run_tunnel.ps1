$logFile = "$env:USERPROFILE\Desktop\tunnel_url.txt"
$proc = Start-Process -NoNewWindow -FilePath "cloudflared" -ArgumentList "tunnel --url http://localhost:8000" -RedirectStandardOutput $logFile -RedirectStandardError $logFile -PassThru
Write-Host "cloudflared PID: $($proc.Id)"
Write-Host "Waiting for URL..."
$timeout = 30
$elapsed = 0
while ($elapsed -lt $timeout) {
    Start-Sleep -Seconds 2
    $content = Get-Content $logFile -Raw
    if ($content -match "https://\S+\.trycloudflare\.com") {
        $url = $matches[0]
        Write-Host "`n=========================================="
        Write-Host "PUBLIC URL: $url"
        Write-Host "=========================================="
        Set-Content -Path "$env:USERPROFILE\Desktop\tunnel_url.txt" -Value $url
        break
    }
    $elapsed += 2
}
Write-Host "`nTunnel is running. Keep this window open."
Write-Host "Press Enter to stop the tunnel..."
Read-Host
$proc.Kill()
