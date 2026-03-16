from typing import Callable, Any

# class BaseTool:
#     \"\"\"
#     A foundational tool class.
#     Agents use tools to interact with external systems or the database.
#     \"\"\"
#     def __init__(self, name: str, description: str, func: Callable):
#         self.name = name
#         self.description = description
#         self.func = func

#     async def execute(self, *args, **kwargs) -> Any:
#         \"\"\"
#         Execute the underlying tool function.
#         \"\"\"
#         return await self.func(*args, **kwargs)
