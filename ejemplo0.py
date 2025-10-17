import asyncio
from agents import Agent, Runner

async def main():
   agent = Agent(
       name="Test Agent",
       instructions="You are a helpful assistant that provides concise responses."
   )
   result = await Runner.run(agent, "Hello! Are you working correctly?")
   print(result.final_output)

if __name__ == "__main__":
   asyncio.run(main())  # Run the async function