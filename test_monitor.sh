#!/bin/bash

echo "🔍 Monitoring for new agent processes..."
echo "Press Ctrl+C to stop"
echo ""

while true; do
    # Check for simple_agent processes
    SIMPLE_AGENT_COUNT=$(ps aux | grep "simple_agent.py" | grep -v grep | wc -l | tr -d ' ')

    # Check for agent.py connect processes
    OLD_AGENT_COUNT=$(ps aux | grep "agent.py connect" | grep -v grep | wc -l | tr -d ' ')

    # Check for multiprocessing workers
    WORKER_COUNT=$(ps aux | grep "multiprocessing.spawn" | grep -v grep | wc -l | tr -d ' ')

    if [ "$SIMPLE_AGENT_COUNT" -gt 0 ] || [ "$OLD_AGENT_COUNT" -gt 0 ] || [ "$WORKER_COUNT" -gt 0 ]; then
        clear
        echo "📊 Agent Process Status ($(date '+%H:%M:%S'))"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "simple_agent.py:      $SIMPLE_AGENT_COUNT processes"
        echo "agent.py connect:     $OLD_AGENT_COUNT processes ❌ (should be 0!)"
        echo "multiprocessing:      $WORKER_COUNT worker processes ❌ (should be 0!)"
        echo ""

        if [ "$SIMPLE_AGENT_COUNT" -eq 1 ] && [ "$OLD_AGENT_COUNT" -eq 0 ] && [ "$WORKER_COUNT" -eq 0 ]; then
            echo "✅ PERFECT! Exactly ONE simple_agent.py running!"
        elif [ "$SIMPLE_AGENT_COUNT" -gt 1 ]; then
            echo "⚠️  WARNING: Multiple simple_agent.py instances!"
        elif [ "$OLD_AGENT_COUNT" -gt 0 ]; then
            echo "❌ ERROR: Old agent.py still spawning!"
        elif [ "$WORKER_COUNT" -gt 0 ]; then
            echo "❌ ERROR: Worker pool still spawning processes!"
        fi

        echo ""
        echo "Active agent processes:"
        ps aux | grep -E "(simple_agent|agent.py connect)" | grep -v grep | awk '{printf "  PID %s: %s\n", $2, substr($0, index($0,$11))}'
    fi

    sleep 1
done
