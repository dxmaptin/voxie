# spawner/run_spawner.py
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from livekit import agents
from spawner_agent import spawner_entrypoint

if __name__ == "__main__":
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=spawner_entrypoint))