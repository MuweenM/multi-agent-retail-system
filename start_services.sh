#!/bin/bash
set -a
source .env
set +a
export PYTHONPATH=$(pwd)

cd services/agent1-intake
uvicorn app.server:app --port 8001 > ../../agent1.log 2>&1 &

cd ../agent2-rootcause
uvicorn app.server:app --port 8002 > ../../agent2.log 2>&1 &

cd ../agent3-retrieval
uvicorn app.server:app --port 8003 > ../../agent3.log 2>&1 &

cd ../agent4-decision
uvicorn app.server:app --port 8004 > ../../agent4.log 2>&1 &

echo "All services started."
