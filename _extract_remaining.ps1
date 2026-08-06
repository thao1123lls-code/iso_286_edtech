$lines = Get-Content 'd:/ISO 286 EdTech/iso_286_edtech/index.html'
$total = $lines.Count
Write-Output "Total lines: $total"
# Write from line 2706 (0-indexed 2705) to end
$start = 2705
$segment = $lines[$start..($total-1)]
$segment | Set-Content 'd:/ISO 286 EdTech/iso_286_edtech/_tail_index.txt' -Encoding UTF8
Write-Output "Wrote tail from line $start"
