from codesys import Agent


# Agents CANNOT see past conversations. You can see this through running this code:


# Initialize with a working directory
agent = Agent(working_dir="./")

# First session - send "hello"
print("First session:")
response1 = agent.run("hello", stream=True)
print("\n")



# Start a new session (this won't know the previous conversation)
print("New session:")
response2 = agent.run("what did i just say?", stream=True)

# Continue the conversation from the previous session
response3 = agent.run_convo("what did i just say?", stream=True)
