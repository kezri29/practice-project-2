class BaseAgent:
    \"\"\"
    A foundational agent class.
    In a real implementation, you would bind this to an LLM provider
    and a state management system like LangGraph or AutoGen.
    \"\"\"
    def __init__(self, name: str, instructions: str):
        self.name = name
        self.instructions = instructions

    async def run(self, input_data: dict) -> dict:
        \"\"\"
        Execute the agent's primary loop.
        \"\"\"
        raise NotImplementedError("Subclasses must implement the run method")
