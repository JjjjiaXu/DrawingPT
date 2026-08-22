$ErrorActionPreference = 'Stop'

$repo = Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')
$outDir = Join-Path $repo 'tmp\deploy'
$bundle = Join-Path $outDir 'drawingpt_server_bundle.tar.gz'
$staging = Join-Path $outDir 'staging'

New-Item -ItemType Directory -Force -Path $outDir | Out-Null
if (Test-Path -LiteralPath $staging) {
  $resolvedStaging = Resolve-Path -LiteralPath $staging
  $resolvedOutDir = Resolve-Path -LiteralPath $outDir
  if (-not $resolvedStaging.Path.StartsWith($resolvedOutDir.Path)) {
    throw "Refusing to delete staging path outside deploy directory: $($resolvedStaging.Path)"
  }
  Remove-Item -LiteralPath $resolvedStaging.Path -Recurse -Force
}
New-Item -ItemType Directory -Force -Path $staging | Out-Null

$trackedTar = Join-Path $outDir 'tracked.tar'
if (Test-Path -LiteralPath $trackedTar) {
  Remove-Item -LiteralPath $trackedTar -Force
}
git -C $repo archive --format=tar -o $trackedTar HEAD
tar -xf $trackedTar -C $staging

$extraDirs = @(
  'third_party\CADTransformer',
  'data\raw\FloorPlanCAD'
)
foreach ($rel in $extraDirs) {
  $src = Join-Path $repo $rel
  $dst = Join-Path $staging $rel
  if (-not (Test-Path -LiteralPath $src)) {
    throw "Missing required deploy path: $src"
  }
  New-Item -ItemType Directory -Force -Path (Split-Path -Parent $dst) | Out-Null
  Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
}

if (Test-Path -LiteralPath $bundle) {
  Remove-Item -LiteralPath $bundle -Force
}
tar -czf $bundle -C $staging .
Get-Item -LiteralPath $bundle | Select-Object FullName,Length
