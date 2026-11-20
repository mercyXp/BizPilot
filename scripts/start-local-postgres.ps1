$ErrorActionPreference = "Stop"
$pgBin = "C:\Program Files\PostgreSQL\18\bin"
$dataDir = Join-Path $PSScriptRoot "..\.data\postgres"
$dataDir = [System.IO.Path]::GetFullPath($dataDir)
$logFile = Join-Path $dataDir "postgres.log"
$port = 55432

if (-not (Test-Path (Join-Path $pgBin "initdb.exe"))) {
    throw "PostgreSQL 18 was not found at $pgBin"
}

New-Item -ItemType Directory -Force -Path $dataDir | Out-Null

if (-not (Test-Path (Join-Path $dataDir "PG_VERSION"))) {
    & "$pgBin\initdb.exe" -D $dataDir -U bizpilot --auth-local=trust --auth-host=trust --encoding=UTF8 --no-locale
    if ($LASTEXITCODE -ne 0) { throw "initdb failed" }
    Add-Content -Path (Join-Path $dataDir "postgresql.conf") "`nlisten_addresses = '127.0.0.1'`nport = $port`n"
}

$running = & "$pgBin\pg_ctl.exe" -D $dataDir status
if ($LASTEXITCODE -ne 0) {
    & "$pgBin\pg_ctl.exe" -D $dataDir -l $logFile -o "-p $port" start
    if ($LASTEXITCODE -ne 0) { throw "pg_ctl start failed" }
}

$dbExists = & "$pgBin\psql.exe" -h 127.0.0.1 -p $port -U bizpilot -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='bizpilot'"
if ($dbExists -ne "1") {
    & "$pgBin\createdb.exe" -h 127.0.0.1 -p $port -U bizpilot bizpilot
    if ($LASTEXITCODE -ne 0) { throw "createdb failed" }
}

Write-Host "PostgreSQL ready on 127.0.0.1:$port database bizpilot"
