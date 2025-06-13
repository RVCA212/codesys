from codesys import Agent

# Initialize with a working directory
agent = Agent(working_dir="/Users/seansullivan/")

# This can be a prompt string or claude code command (treat it as your claude code input)
lines = agent.run("""given this is a mac, open safari and go to google.com""", stream=True)