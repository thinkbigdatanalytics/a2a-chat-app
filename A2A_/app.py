import os
import streamlit as st
import psycopg2
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from google.adk.tools import google_search
from google.adk.tools.mcp_tool import MCPTool
import asyncio
from google.adk.tools.mcp_tool.mcp_session_manager import MCPSessionManager

from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters

os.environ["GOOGLE_API_KEY"] = "GOOGLE KEY"

APP_NAME = "streamlit_adk"
USER_ID = "user"
SESSION_ID = "session_1"

class SimpleTool:
    def __init__(self, name, description, func):
        self.name = name
        self.description = description
        self.func = func

    async def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)
    
def run_sql_query(sql_query: str) -> str:
    try:
        conn = psycopg2.connect(
            dbname="sample_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432
        )
        cur = conn.cursor()
        cur.execute(sql_query)
        if cur.description: 
            result = cur.fetchall()
        else:
            conn.commit()
            result = "Query executed successfully."
        cur.close()
        conn.close()
        return str(result)
    except Exception as e:
        return f"Error running query: {e}"

run_sql_query.__doc__ = "Run SQL queries on the sample_db PostgreSQL database"

agent = Agent(
    name="streamlit_agent",
    model="gemini-2.5-flash",
    instruction="You are a helpful assistant."
)


github_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command="node",
            args=["D:/Anish/New folder/ADK_2/MCP/server.js"],
            env={
                "GITHUB_TOKEN": "git token"
            }
        )
    )
)
github_agent = Agent(
    name="github_agent",
    model="gemini-2.5-pro",
    instruction="You are a GitHub assistant. Use the MCP tool to manage repos and issues.",
    tools=[github_toolset],
)

flight_agent = Agent(
    name="flight_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a helpful assistant specializing in flight bookings and travel. "
        "You help users find flights, check schedules, prices, baggage rules, "
        "and provide travel tips related to flights."
    ),
    tools=[google_search]
)

hotel_agent = Agent(
    name="hotel_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are an expert hotel booking assistant. You help users find hotels, "
        "compare prices, check availability, recommend amenities, and answer "
        "questions about hotel stays."
    ),
    tools=[google_search]
)

car_rental_agent = Agent(
    name="car_rental_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a knowledgeable car rental assistant. You assist users with "
        "finding rental cars, comparing prices, rental policies, insurance options, "
        "and pick-up/drop-off locations."
    ),
    tools=[google_search]
)

weather_agent = Agent(
    name="weather_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a weather assistant. You provide up-to-date weather forecasts, "
        "alerts, and travel weather advice for specific locations and dates."
    ),
    tools=[google_search]
)

run_sql_query.__doc__ = "Run SQL queries on the sample_db PostgreSQL database"

postgres_agent = Agent(
    name="postgres_agent",
    model="gemini-2.5-flash",
    instruction=(
        "You are a database assistant. You accept natural language requests and convert them "
        "into SQL queries to retrieve or modify data in a real-time Postgres database. "
        "Answer the user with the data retrieved or any errors."
    ),
    tools=[run_sql_query] 
)


session_service = InMemorySessionService()
session_service.create_session_sync(
    app_name=APP_NAME,
    user_id=USER_ID,
    session_id=SESSION_ID
)


# session_service = InMemorySessionService()
# session_service.create_session_sync(
#     app_name=APP_NAME,
#     user_id=USER_ID,
#     session_id=SESSION_ID
# )

runner_postgres = Runner(
    app_name=APP_NAME,
    agent=postgres_agent,
    session_service=session_service
)

runner_github = Runner(
    app_name=APP_NAME,
    agent=github_agent,
    session_service=session_service
)

runner_general = Runner(
    app_name=APP_NAME,
    agent=agent,
    session_service=session_service
)
runner_flight = Runner(
    app_name=APP_NAME,
    agent=flight_agent,
    session_service=session_service
)
runner_hotel = Runner(
    app_name=APP_NAME,
    agent=hotel_agent,
    session_service=session_service
)
runner_car = Runner(
    app_name=APP_NAME,
    agent=car_rental_agent,
    session_service=session_service
)
runner_weather = Runner(
    app_name=APP_NAME,
    agent=weather_agent,
    session_service=session_service
)

def run_sql_query(sql_query):
    try:
        conn = psycopg2.connect(
            dbname="sample_db",
            user="postgres",
            password="postgres",
            host="localhost",
            port=5432
        )
        with conn.cursor() as cur:
            cur.execute(sql_query)
            # Try to fetch results only if it's a SELECT
            if sql_query.strip().lower().startswith("select"):
                rows = cur.fetchall()
                conn.close()
                return str(rows) if rows else "Query executed successfully, no rows returned."
            else:
                conn.commit()
                conn.close()
                return "Query executed successfully."
    except Exception as e:
        return f"Error running query: {e}"

def choose_agent_and_runner(user_text):
    user_text_lower = user_text.lower()
    if any(word in user_text_lower for word in ["flight", "airline", "plane", "ticket", "departure", "arrival", "baggage"]):
        return runner_flight, None
    elif any(word in user_text_lower for word in ["hotel", "room", "stay", "check-in", "checkout", "amenities"]):
        return runner_hotel, None
    elif any(word in user_text_lower for word in ["car", "rental", "rent", "vehicle", "insurance", "pickup", "dropoff"]):
        return runner_car, None
    elif any(word in user_text_lower for word in ["weather", "forecast", "temperature", "rain", "snow", "storm", "sunny"]):
        return runner_weather, None
    elif any(word in user_text_lower for word in ["database", "db", "data", "sql", "query", "table", "record", "user", "insert", "select", "update", "delete"]):
        return runner_postgres,None
    elif any(word in user_text_lower for word in ["github", "repo", "repository", "commit", "push", "branch", "pull request", "issue", "pr"]):
        return runner_github, None 
    else:
        return runner_general, None


st.title("Assistant Chat")

if "messages" not in st.session_state:
    st.session_state.messages = []

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_msg := st.chat_input("Type your message..."):
    st.session_state.messages.append({"role": "user", "content": user_msg})
    st.chat_message("user").markdown(user_msg)

    runner, is_postgres = choose_agent_and_runner(user_msg)

    content = types.Content(role="user", parts=[types.Part(text=user_msg)])

    events = runner.run(
        user_id=USER_ID,
        session_id=SESSION_ID,
        new_message=content
    )

    assistant_reply = ""
    for ev in events:
        if ev.is_final_response():
            assistant_reply = ev.content.parts[0].text

    st.session_state.messages.append({"role": "assistant", "content": assistant_reply})
    st.chat_message("assistant").markdown(assistant_reply)

