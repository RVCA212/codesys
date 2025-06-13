from codesys import Agent
import os

working_dir = os.getcwd()


agent = Agent(working_dir=working_dir)


agent.run("hello, my name is sean", stream=True)

bash_only_response = agent.run_with_tools(
	prompt="what was my last query?",
    tools=["Bash"],
	stream=True,
    continue_session=True,
)


