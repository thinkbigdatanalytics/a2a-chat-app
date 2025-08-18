import asyncio
from google.adk.agents import SequentialAgent
from toolsets import add_toolset, sub_toolset, mul_toolset, div_toolset
from agent_factory import toolset_to_agent

async def create_main_agent():
    add_agent = await toolset_to_agent(add_toolset, "Add_Agent")
    sub_agent = await toolset_to_agent(sub_toolset, "Sub_Agent")
    mul_agent = await toolset_to_agent(mul_toolset, "Mul_Agent")
    div_agent = await toolset_to_agent(div_toolset, "Div_Agent")

    return SequentialAgent(
        name="Math_Master_Agent",
        sub_agents=[add_agent, sub_agent, mul_agent, div_agent],
    )

async def run_cli():
    main_agent = await create_main_agent()

    print("🤖 Math Agent CLI (type 'exit' to quit)")
    while True:
        query = input(">> ")
        if query.strip().lower() == "exit":
            break
        try:
            response = await main_agent.run(query)
            print("Answer:", response)
        except Exception as e:
            print("Error:", str(e))

if __name__ == "__main__":
    asyncio.run(run_cli())
