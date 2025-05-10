# File: C:\path\to\activityLog.ps1
$filePath = 'C:\Users\tokri\Downloads\steadi-app\test.js'
$loopCount = 1

while ($true) {
    # wait 2 seconds
    Start-Sleep -Seconds 2

    # build our timestamped log line
    $timeStamp = Get-Date -Format 'yyyy-MM-dd HH:mm:ss'
    $logLine   = "console.log('Activity tracked: $loopCount - $timeStamp');"

    # 1) append the log
    Add-Content -Path $filePath -Value $logLine

    # 2) on every 5th append, strip out lines 2-4 of the batch
    if ($loopCount % 5 -eq 0) {
        # read all lines
        $allLines = Get-Content -Path $filePath
        $total    = $allLines.Count

        # compute how many lines to keep (never less than 1)
        $keep     = [Math]::Max($total - 4, 1)

        # take only the first $keep lines
        $keptLines = $allLines[0..($keep - 1)]

        # overwrite file with the kept lines
        Set-Content -Path $filePath -Value $keptLines

        # re-append the 5th log of this batch
        Add-Content -Path $filePath -Value $logLine
    }

    $loopCount++
}
