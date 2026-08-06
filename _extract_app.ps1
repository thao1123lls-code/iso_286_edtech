$lines = Get-Content 'd:/ISO 286 EdTech/iso_286_edtech/index.html'
for ($i = 3120; $i -le 3283; $i++) {
    Write-Output ("{0}: {1}" -f ($i + 1), $lines[$i])
}
