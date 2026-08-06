$lines = Get-Content 'd:/ISO 286 EdTech/iso_286_edtech/index.html'
Write-Output "=========== MOCK_USERS (277-360) ==========="
for ($i = 276; $i -le 359; $i++) {
    Write-Output ("{0}: {1}" -f ($i + 1), $lines[$i])
}
Write-Output "=========== APP/LOGIN (3140-3290) ==========="
for ($i = 3139; $i -le 3289; $i++) {
    Write-Output ("{0}: {1}" -f ($i + 1), $lines[$i])
}
