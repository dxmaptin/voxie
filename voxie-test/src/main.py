# spawner/main.py
from spawner_agent import spawner_entrypoint

if __name__ == "__main__":
    from livekit import agents
    agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=spawner_entrypoint))