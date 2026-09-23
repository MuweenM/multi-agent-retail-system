#!/usr/bin/env bash
# run_local.sh - A script to start the 4 agents and run a test curl request

# Ensure we're in the project root
if [ ! -f .env ]; then
  echo "Error: .env file not found. Copying .env.example..."
  cp .env.example .env
fi

export PYTHONPATH="$(pwd):$(pwd)/shared"

echo "Starting Agent 1 (Intake) on port 8001..."
python -m services.agent1-intake.app.server > agent1.log 2>&1 &
PID1=$!

echo "Starting Agent 2 (Root Cause) on port 8002..."
python -m services.agent2-rootcause.app.server > agent2.log 2>&1 &
PID2=$!

echo "Starting Agent 3 (Retrieval) on port 8003..."
python -m services.agent3-retrieval.app.server > agent3.log 2>&1 &
PID3=$!

echo "Starting Agent 4 (Decision) on port 8004..."
python -m services.agent4-decision.app.server > agent4.log 2>&1 &
PID4=$!

echo "Waiting 5 seconds for servers to start..."
sleep 5

echo "----------------------------------------"
echo "Running curl test against Agent 4..."
echo "----------------------------------------"
curl -s -X POST localhost:8004/api/v1/returns \
  -H "Content-Type: application/json" \
  -d '{"text":"phone battery dies fast"}'

echo -e "\n\nShutting down agents..."
kill -9 $PID1 $PID2 $PID3 $PID4
echo "Done."
