from codesys import Agent

# Initialize with a working directory
agent = Agent(working_dir="/Users/seansullivan/lmsys-sdk/")

# Run Claude with a prompt and automatically print streaming output
lines = agent.run("""hello""", stream=True)

# Continue the conversation from the previous session
continuation = agent.run_convo("""What did I just say?""", stream=True)

# Get the session ID from the last run (useful if you want to resume later)
session_id = agent.get_last_session_id()
if session_id:
    print(f"\nSession ID: {session_id}")

    # To resume a specific session by ID
    # resumed_response = agent.resume_session(session_id, """Continue our discussion.""", stream=True)
