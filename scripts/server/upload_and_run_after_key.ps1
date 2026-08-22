$ErrorActionPreference = 'Stop'

$repo = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')

function Require-Env([string]$name) {
  $value = [Environment]::GetEnvironmentVariable($name, 'Process')
  if ([string]::IsNullOrWhiteSpace($value)) {
    $value = [Environment]::GetEnvironmentVariable($name, 'User')
  }
  if ([string]::IsNullOrWhiteSpace($value)) {
    throw "Missing required environment variable: $name"
  }
  return $value
}

$key = if ($env:DRAWINGPT_SSH_KEY) { $env:DRAWINGPT_SSH_KEY } else { Join-Path $env:USERPROFILE '.ssh\drawingpt_server_ed25519' }
$hostName = Require-Env 'DRAWINGPT_SSH_HOST'
$port = if ($env:DRAWINGPT_SSH_PORT) { $env:DRAWINGPT_SSH_PORT } else { '22' }
$user = Require-Env 'DRAWINGPT_SSH_USER'
$remoteProject = if ($env:DRAWINGPT_REMOTE_PROJECT) { $env:DRAWINGPT_REMOTE_PROJECT } else { "~/data/users/$user/DrawingPT" }
$remoteScratch = if ($env:DRAWINGPT_REMOTE_SCRATCH) { $env:DRAWINGPT_REMOTE_SCRATCH } else { "~/data/scratch/$user/DrawingPT" }
$bundle = Join-Path $repo 'tmp\deploy\drawingpt_server_bundle.tar.gz'

if (-not (Test-Path -LiteralPath $key)) {
  throw "SSH key not found: $key"
}
if (-not (Test-Path -LiteralPath $bundle)) {
  throw "Bundle not found. Run scripts/server/make_server_bundle.ps1 first."
}

Write-Host "[upload] testing key-based SSH"
ssh -i $key -p $port -o BatchMode=yes -o ConnectTimeout=10 "$user@$hostName" "echo key-login-ok"

Write-Host "[upload] creating remote directories"
ssh -i $key -p $port "$user@$hostName" "mkdir -p $remoteProject $remoteScratch/upload"

Write-Host "[upload] copying bundle"
scp -i $key -P $port $bundle "$user@$hostName`:$remoteScratch/upload/drawingpt_server_bundle.tar.gz"

Write-Host "[remote] extracting and running safe setup"
ssh -i $key -p $port "$user@$hostName" @"
set -euo pipefail
mkdir -p $remoteProject $remoteScratch/upload
tar -xzf $remoteScratch/upload/drawingpt_server_bundle.tar.gz -C $remoteProject
cd $remoteProject
bash scripts/server/yao_remote_probe.sh
bash scripts/server/yao_bootstrap.sh
bash scripts/server/prepare_cadtransformer_data.sh
mkdir -p logs/slurm
sbatch scripts/server/cadtransformer_smoke.sbatch
"@
