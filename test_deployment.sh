#!/bin/bash

# Test script for Exercise 4 - Backend Deployment
# Tests the deployed backend at https://voxie-1.railway.app

BACKEND_URL="https://voxie-1.railway.app"

echo "🧪 Testing Voxie Backend Deployment"
echo "=================================="
echo ""

# Test 1: Health Check
echo "Test 1: Health Check"
echo "--------------------"
echo "GET ${BACKEND_URL}/"
echo ""

HEALTH_RESPONSE=$(curl -s "${BACKEND_URL}/")
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

if echo "$HEALTH_RESPONSE" | grep -q "\"status\".*:.*\"ok\""; then
    echo "✅ Health check passed"
else
    echo "❌ Health check failed"
    exit 1
fi

echo ""
echo "-----------------------------------"
echo ""

# Test 2: Agents API
echo "Test 2: Agents API"
echo "------------------"
echo "GET ${BACKEND_URL}/api/agents"
echo ""

AGENTS_RESPONSE=$(curl -s "${BACKEND_URL}/api/agents")
echo "$AGENTS_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$AGENTS_RESPONSE"

if echo "$AGENTS_RESPONSE" | grep -q "\"status\".*:.*\"success\""; then
    AGENT_COUNT=$(echo "$AGENTS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('count', 0))" 2>/dev/null || echo "0")
    echo "✅ Agents API passed - Found $AGENT_COUNT agents"
else
    echo "❌ Agents API failed"
    exit 1
fi

echo ""
echo "-----------------------------------"
echo ""

# Summary
echo "🎉 All Tests Passed!"
echo ""
echo "Your backend is live at: ${BACKEND_URL}"
echo ""
echo "Next steps:"
echo "1. Open simple_call_interface_cloud.html"
echo "2. Backend URL is pre-filled: ${BACKEND_URL}"
echo "3. Click 'Load Agents'"
echo "4. Select an agent and click 'Start Call'"
echo "5. Speak with your cloud-deployed agent!"
echo ""
echo "For more info, see EXERCISE_4_QUICKSTART.md"
