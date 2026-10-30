param(
    [Parameter(Mandatory=$true)][string]$Executable,
    [int]$Width = 1280,
    [int]$Height = 720,
    [int]$Frames = 10800
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path -LiteralPath $Executable -PathType Leaf)) { throw 'Packaged executable missing' }
if (Get-Process UnrealEditor -ErrorAction SilentlyContinue) { throw 'Close editor before profiling' }
$reportDir = 'C:\BeybladeUE\Saved\QA85'
New-Item -ItemType Directory -Path $reportDir -Force | Out-Null
$name = "Perf85_${Width}x${Height}"
$logPath = Join-Path $reportDir "$name.log"
$commands = "t.MaxFPS 60,csvprofile STARTFILE=$name,csvprofile EXITONCOMPLETION,csvprofile FRAMES=$Frames"
$arguments = @('-windowed', "-ResX=$Width", "-ResY=$Height", '-ForceRes', '-novsync',
    '-unattended', '-ProtoSeed=4242', '-ProtoAuto=999', '-csvCompression=0',
    "-abslog=$logPath", ('-ExecCmds="' + $commands + '"'))
$gameProcess = Start-Process -FilePath $Executable -ArgumentList $arguments -PassThru
$timer = [Diagnostics.Stopwatch]::StartNew()
$samples = [Collections.Generic.List[object]]::new()
while (-not $gameProcess.HasExited) {
    $gameProcess.Refresh()
    if (-not $gameProcess.HasExited) {
        $samples.Add([pscustomobject]@{
            elapsed_s = [math]::Round($timer.Elapsed.TotalSeconds, 3)
            working_set_mb = [math]::Round($gameProcess.WorkingSet64 / 1MB, 3)
            private_mb = [math]::Round($gameProcess.PrivateMemorySize64 / 1MB, 3)
            cpu_s = [math]::Round($gameProcess.TotalProcessorTime.TotalSeconds, 3)
        })
    }
    Start-Sleep -Seconds 1
}
$timer.Stop()
$samples | Export-Csv -LiteralPath (Join-Path $reportDir "$name-memory.csv") -NoTypeInformation -Encoding utf8
$metadata = @{executable=$Executable; width=$Width; height=$Height; target_fps=60;
    requested_frames=$Frames; wall_seconds=$timer.Elapsed.TotalSeconds; exit_code=$gameProcess.ExitCode;
    samples=$samples.Count; log=$logPath; note='Auto999 keeps battles running; CSV completion ends this performance test.'}
[IO.File]::WriteAllText((Join-Path $reportDir "$name-run.json"), ($metadata | ConvertTo-Json), [Text.UTF8Encoding]::new($false))
if ($samples.Count -lt 10) { throw 'Performance run too short; inspect game log' }
if (-not (Select-String -LiteralPath $logPath -Pattern 'Capture Ended' -Quiet)) { throw 'CSV capture did not finish; inspect game log' }
Write-Output "PROFILE_COMPLETE $name samples=$($samples.Count) seconds=$([math]::Round($timer.Elapsed.TotalSeconds,1))"
