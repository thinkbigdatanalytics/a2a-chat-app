import asyncio
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from agents.main_math_agent import main_math_agent
import os
APP_NAME = "math_app"
USER_ID = "user1"
os.environ["GOOGLE_API_KEY"] = "AIzaSyAoZE9lxGoHyZVituaH9KRXcV5GO1Qn900"

async def main():
    session_service = InMemorySessionService()
    session = await session_service.create_session(app_name=APP_NAME, user_id=USER_ID)
    session_id = session.id

    runner = Runner(app_name=APP_NAME, agent=main_math_agent, session_service=session_service)

    print("Math Agent Ready! Type 'exit' to quit.")
    while True:
        user_input = input("You: ")
        if user_input.lower() in ["exit", "quit"]:
            break

        content = types.Content(role="user", parts=[types.Part(text=user_input)])
        events = runner.run(user_id=USER_ID, session_id=session_id, new_message=content)

        for ev in events:
            if ev.is_final_response() and ev.content and ev.content.parts:
                print("AI:", ev.content.parts[0].text)
                break

if __name__ == "__main__":
    asyncio.run(main())
    
