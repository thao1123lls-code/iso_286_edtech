param([int]$Start=2834, [int]$End=3015)
$arr = Get-Content 'd:/iso-286-edtech/index.html'
for ($i = $Start-1; $i -lt $End -and $i -lt $arr.Count; $i++) {
    Write-Output ("{0,5}| {1}" -f ($i+1), $arr[$i])
}
