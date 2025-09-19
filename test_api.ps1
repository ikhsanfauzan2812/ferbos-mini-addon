# PowerShell test script for Ferbos Mini Addon API

# Configuration
$HA_IP = "localhost"
$PORT = "8080"
$BASE_URL = "http://${HA_IP}:${PORT}"

Write-Host "🚀 Testing Ferbos Mini Addon API" -ForegroundColor Blue
Write-Host "Base URL: $BASE_URL" -ForegroundColor Blue
Write-Host "==================================" -ForegroundColor Blue

# Function to test endpoint
function Test-Endpoint {
    param(
        [string]$Method,
        [string]$Endpoint,
        [string]$Data = $null
    )
    
    Write-Host "`n🔍 $Method $Endpoint" -ForegroundColor Yellow
    
    try {
        if ($Method -eq "GET") {
            $response = Invoke-RestMethod -Uri "${BASE_URL}${Endpoint}" -Method Get -TimeoutSec 10
        } elseif ($Method -eq "POST") {
            $response = Invoke-RestMethod -Uri "${BASE_URL}${Endpoint}" -Method Post -Body $Data -ContentType "application/json" -TimeoutSec 10
        }
        
        Write-Host "   ✅ Success" -ForegroundColor Green
        $response | ConvertTo-Json -Depth 3
    }
    catch {
        Write-Host "   ❌ Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# Test 1: Health Check
Test-Endpoint -Method "GET" -Endpoint "/health"

# Test 2: Get Tables
Test-Endpoint -Method "GET" -Endpoint "/tables"

# Test 3: Get Entities
Test-Endpoint -Method "GET" -Endpoint "/entities"

# Test 4: Get Recent States
Test-Endpoint -Method "GET" -Endpoint "/states?limit=5"

# Test 5: Get Recent Events
Test-Endpoint -Method "GET" -Endpoint "/events?limit=5"

# Test 6: Custom Query - Get all entities
$query1 = @{
    query = "SELECT DISTINCT entity_id FROM states ORDER BY entity_id LIMIT 10"
    params = @()
} | ConvertTo-Json
Test-Endpoint -Method "POST" -Endpoint "/query" -Data $query1

# Test 7: Custom Query - Get 'on' states
$query2 = @{
    query = "SELECT entity_id, state, last_updated FROM states WHERE state = ? ORDER BY last_updated DESC LIMIT 5"
    params = @("on")
} | ConvertTo-Json
Test-Endpoint -Method "POST" -Endpoint "/query" -Data $query2

# Test 8: Custom Query - Get sensor entities
$query3 = @{
    query = "SELECT entity_id, state FROM states WHERE entity_id LIKE ? ORDER BY entity_id LIMIT 10"
    params = @("sensor.%")
} | ConvertTo-Json
Test-Endpoint -Method "POST" -Endpoint "/query" -Data $query3

Write-Host "`n✅ All tests completed!" -ForegroundColor Green
Write-Host "💡 Tip: Use 'python test_api.py' for interactive mode" -ForegroundColor Blue
