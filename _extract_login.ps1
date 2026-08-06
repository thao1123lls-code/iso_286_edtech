$lines = Get-Content 'd:/ISO 286 EdTech/iso_286_edtech/index.html'
for ($i = 2893; $i -le 3119; $i++) {
    Write-Output ("{0}: {1}" -f ($i + 1), $lines[$i])
}
