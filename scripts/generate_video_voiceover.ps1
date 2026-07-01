param(
    [string]$SubtitlePath = "docs/video_subtitles.srt",
    [string]$OutputDir = "docs/video_voiceover_clips",
    [string]$VoiceName = "Microsoft Huihui Desktop",
    [int]$Rate = 0
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Add-Type -AssemblyName System.Speech

function Parse-SrtTime {
    param([string]$Value)

    $parts = $Value.Trim() -split "[:,]"
    if ($parts.Count -ne 4) {
        throw "Invalid SRT time: $Value"
    }

    return [TimeSpan]::FromHours([int]$parts[0]) +
        [TimeSpan]::FromMinutes([int]$parts[1]) +
        [TimeSpan]::FromSeconds([int]$parts[2]) +
        [TimeSpan]::FromMilliseconds([int]$parts[3])
}

function Parse-SrtFile {
    param([string]$Path)

    $content = [System.IO.File]::ReadAllText((Resolve-Path $Path), [System.Text.Encoding]::UTF8)
    $blocks = [System.Text.RegularExpressions.Regex]::Split($content.Trim(), "\r?\n\r?\n")
    $items = @()

    foreach ($block in $blocks) {
        if ([string]::IsNullOrWhiteSpace($block)) {
            continue
        }

        $lines = $block -split "\r?\n"
        if ($lines.Count -lt 3) {
            continue
        }

        $index = [int]$lines[0].Trim()
        $timeParts = $lines[1] -split "\s+-->\s+"
        $text = (($lines[2..($lines.Count - 1)] | ForEach-Object { $_.Trim() }) -join " ").Trim()

        $items += [PSCustomObject]@{
            Index = $index
            Start = Parse-SrtTime $timeParts[0]
            End = Parse-SrtTime $timeParts[1]
            Text = $text
        }
    }

    return $items
}

function New-SystemSpeechSpeaker {
    param(
        [string]$RequestedVoice,
        [int]$RequestedRate
    )

    $speaker = New-Object System.Speech.Synthesis.SpeechSynthesizer
    $speaker.Rate = $RequestedRate

    $installedVoices = $speaker.GetInstalledVoices() | ForEach-Object { $_.VoiceInfo.Name }
    if ($RequestedVoice -and ($installedVoices -contains $RequestedVoice)) {
        try {
            $speaker.SelectVoice($RequestedVoice)
        } catch {
            Write-Warning "System.Speech failed to select voice '$RequestedVoice'. Falling back to the default installed voice."
        }
    }

    return $speaker
}

if (-not (Test-Path $SubtitlePath)) {
    throw "Subtitle file not found: $SubtitlePath"
}

New-Item -ItemType Directory -Force -Path $OutputDir | Out-Null

$segments = Parse-SrtFile -Path $SubtitlePath
$speaker = New-SystemSpeechSpeaker -RequestedVoice $VoiceName -RequestedRate $Rate

$manifest = New-Object System.Collections.Generic.List[object]

try {
    foreach ($segment in $segments) {
        $fileName = "{0:d2}.wav" -f $segment.Index
        $outputPath = Join-Path $OutputDir $fileName

        $speaker.SetOutputToWaveFile($outputPath)
        $speaker.Speak($segment.Text)
        $speaker.SetOutputToNull()

        $manifest.Add([PSCustomObject]@{
            Index = $segment.Index
            Start = $segment.Start.ToString()
            End = $segment.End.ToString()
            DurationSeconds = [math]::Round(($segment.End - $segment.Start).TotalSeconds, 3)
            AudioFile = $fileName
            Text = $segment.Text
        }) | Out-Null
    }
} catch {
    throw @"
Voice generation failed in the current environment.

Likely causes:
1. Windows TTS is restricted by the current shell security context.
2. The requested voice is not available to this PowerShell session.
3. The environment allows voice enumeration but blocks synthesis.

You can still use:
- docs/video_subtitles.srt
- docs/video_voiceover_script.md

Error detail:
$($_.Exception.Message)
"@
} finally {
    $speaker.Dispose()
}

$manifestPath = Join-Path $OutputDir "manifest.csv"
$manifest | Export-Csv -NoTypeInformation -Encoding UTF8 -Path $manifestPath

Write-Output "Generated $($segments.Count) voiceover clips in $OutputDir"
Write-Output "Manifest saved to $manifestPath"
