# Flow MCP one-time setup for Windows (from https://github.com/GTAI-1/flow-mcp)
# Run: right-click this file > "Run with PowerShell"
$ErrorActionPreference = "Stop"
function Refresh-Path { $env:Path = [Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [Environment]::GetEnvironmentVariable("Path","User") }
function Need($cmd, $wingetId) {
  if (-not (Get-Command $cmd -ErrorAction SilentlyContinue)) {
    Write-Host "Installing $wingetId ..." -ForegroundColor Cyan
    winget install -e --id $wingetId --accept-source-agreements --accept-package-agreements
    Refresh-Path
  } else { Write-Host "$cmd found" -ForegroundColor Green }
}

Write-Host "`n[1/5] Checking helper programs" -ForegroundColor Yellow
Need git    "Git.Git"
Need node   "OpenJS.NodeJS.LTS"
Need ffmpeg "Gyan.FFmpeg"
$chrome = @("$env:ProgramFiles\Google\Chrome\Application\chrome.exe","${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe","$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe") | Where-Object { Test-Path $_ }
if (-not $chrome) { winget install -e --id Google.Chrome --accept-source-agreements --accept-package-agreements } else { Write-Host "Chrome found" -ForegroundColor Green }
$nodeMajor = [int]((node --version).TrimStart("v").Split(".")[0])
if ($nodeMajor -lt 22) { winget upgrade -e --id OpenJS.NodeJS.LTS; Refresh-Path }

Write-Host "`n[2/5] Downloading Flow MCP into $HOME\flow-mcp" -ForegroundColor Yellow
$dir = Join-Path $HOME "flow-mcp"
if (Test-Path $dir) { git -C $dir pull } else { git clone https://github.com/GTAI-1/flow-mcp.git $dir }

Write-Host "`n[3/5] Installing and building" -ForegroundColor Yellow
Push-Location $dir
npm install
npm run build
Pop-Location

Write-Host "`n[4/5] Connecting Flow MCP to the Claude desktop app" -ForegroundColor Yellow
$entry = Join-Path $dir "dist\index.js"
$cfgDirs = @("$env:APPDATA\Claude")
Get-ChildItem "$env:LOCALAPPDATA\Packages" -Directory -Filter "Claude_*" -ErrorAction SilentlyContinue | ForEach-Object { $cfgDirs += (Join-Path $_.FullName "LocalCache\Roaming\Claude") }
foreach ($d in $cfgDirs) {
  if (-not (Test-Path $d)) { continue }
  $cfg = Join-Path $d "claude_desktop_config.json"
  if (Test-Path $cfg) { Copy-Item $cfg "$cfg.bak" -Force; $json = Get-Content $cfg -Raw | ConvertFrom-Json } else { $json = [pscustomobject]@{} }
  if (-not $json.PSObject.Properties["mcpServers"]) { $json | Add-Member -NotePropertyName mcpServers -NotePropertyValue ([pscustomobject]@{}) }
  $server = [pscustomobject]@{ command = "node"; args = @($entry) }
  if ($json.mcpServers.PSObject.Properties["flow"]) { $json.mcpServers.flow = $server } else { $json.mcpServers | Add-Member -NotePropertyName flow -NotePropertyValue $server }
  [IO.File]::WriteAllText($cfg, ($json | ConvertTo-Json -Depth 20), (New-Object System.Text.UTF8Encoding $false))
  Write-Host "Updated $cfg (backup saved as .bak)" -ForegroundColor Green
}
if (Get-Command claude -ErrorAction SilentlyContinue) { claude mcp add --scope user flow -- node $entry }

Write-Host "`n[5/5] Opening Flow's own Chrome window for your one-time Google sign-in" -ForegroundColor Yellow
Write-Host "Sign in, open (or create) a Flow project, and LEAVE THAT WINDOW OPEN." -ForegroundColor Magenta
Push-Location $dir
npm run login
Pop-Location
Write-Host "`nDone. Fully quit Claude (system tray > Quit) and reopen it." -ForegroundColor Green
Read-Host "Press Enter to close"
