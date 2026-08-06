   $lines = Get-Content 'd:/ISO 286 EdTech/iso_286_edtech/index.html'
for ($i = 1468; $i -le 1530; $i++) {
    Write-Output ("{0}: {1}" -f ($i + 1), $lines[$i])
}
