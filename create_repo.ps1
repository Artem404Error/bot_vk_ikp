$body = @{
    name = 'bot_vk_ikp'
    description = 'VK Sales Bot'
    private = $false
} | ConvertTo-Json

$bytes = [System.Text.Encoding]::UTF8.GetBytes($body)

$headers = @{
    'Authorization' = 'Bearer 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'
    'Accept' = 'application/vnd.github.v3+json'
}

$result = Invoke-RestMethod -Method POST -Uri 'https://api.github.com/user/repos' -Headers $headers -Body $bytes -ContentType 'application/json; charset=utf-8'
Write-Host "Repository created: $($result.html_url)"