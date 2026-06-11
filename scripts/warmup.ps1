# Warmup ping for the chatbot — keeps the LLM + embed models resident in Ollama
# and primes the snapshot caches. Run every ~10 minutes via Windows Task
# Scheduler so the first user-facing request never pays the 14s cold-load tax.
#
# Register example (run in admin PowerShell, edit URL + TOKEN to match .env):
#   $action  = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -ExecutionPolicy Bypass -File `"D:\Projects\Rhize Dashboard\chat_bot\scripts\warmup.ps1`""
#   $trigger = New-ScheduledTaskTrigger -Once -At (Get-Date) -RepetitionInterval (New-TimeSpan -Minutes 10)
#   Register-ScheduledTask -TaskName "rhize-chatbot-warmup" -Action $action -Trigger $trigger -RunLevel Highest
#
# Linux equivalent (cron):
#   */10 * * * * curl -s -X POST -H "Authorization: Bearer $TOKEN" http://127.0.0.1:8000/warmup >/dev/null

param(
  [string]$Url   = $env:CHATBOT_WARMUP_URL,
  [string]$Token = $env:CHATBOT_SERVICE_TOKEN
)

if (-not $Url)   { $Url   = "http://127.0.0.1:8000/warmup" }
if (-not $Token) { $Token = "" }

$headers = @{ }
if ($Token) { $headers["Authorization"] = "Bearer $Token" }

try {
  $r = Invoke-RestMethod -Method Post -Uri $Url -Headers $headers -TimeoutSec 60
  "$(Get-Date -Format o) ok elapsed_ms=$($r.elapsed_ms) fp=$($r.fast_path_rows) ex=$($r.example_rows) sc=$($r.schema_rows)" |
    Out-File -FilePath "$PSScriptRoot\..\logs\warmup.log" -Append -Encoding utf8
} catch {
  "$(Get-Date -Format o) FAIL $($_.Exception.Message)" |
    Out-File -FilePath "$PSScriptRoot\..\logs\warmup.log" -Append -Encoding utf8
  exit 1
}
