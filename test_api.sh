#!/bin/bash
# Simple test script for Ferbos Mini Addon API

# Configuration
HA_IP="localhost"
PORT="8080"
BASE_URL="http://${HA_IP}:${PORT}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Testing Ferbos Mini Addon API${NC}"
echo -e "${BLUE}Base URL: ${BASE_URL}${NC}"
echo "=================================="

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    
    echo -e "\n${YELLOW}🔍 ${method} ${endpoint}${NC}"
    
    if [ "$method" = "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" "${BASE_URL}${endpoint}")
    elif [ "$method" = "POST" ]; then
        response=$(curl -s -w "\n%{http_code}" -X POST -H "Content-Type: application/json" -d "$data" "${BASE_URL}${endpoint}")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | head -n -1)
    
    if [ "$http_code" = "200" ]; then
        echo -e "${GREEN}   ✅ Success (${http_code})${NC}"
        echo "$body" | jq . 2>/dev/null || echo "$body"
    else
        echo -e "${RED}   ❌ Error (${http_code})${NC}"
        echo "$body"
    fi
}

# Test 1: Health Check
test_endpoint "GET" "/health"

# Test 2: Get Tables
test_endpoint "GET" "/tables"

# Test 3: Get Entities
test_endpoint "GET" "/entities"

# Test 4: Get Recent States
test_endpoint "GET" "/states?limit=5"

# Test 5: Get Recent Events
test_endpoint "GET" "/events?limit=5"

# Test 6: Custom Query - Get all entities
test_endpoint "POST" "/query" '{"query": "SELECT DISTINCT entity_id FROM states ORDER BY entity_id LIMIT 10", "params": []}'

# Test 7: Custom Query - Get 'on' states
test_endpoint "POST" "/query" '{"query": "SELECT entity_id, state, last_updated FROM states WHERE state = ? ORDER BY last_updated DESC LIMIT 5", "params": ["on"]}'

# Test 8: Custom Query - Get sensor entities
test_endpoint "POST" "/query" '{"query": "SELECT entity_id, state FROM states WHERE entity_id LIKE ? ORDER BY entity_id LIMIT 10", "params": ["sensor.%"]}'

echo -e "\n${GREEN}✅ All tests completed!${NC}"
echo -e "${BLUE}💡 Tip: Use 'python test_api.py' for interactive mode${NC}"
