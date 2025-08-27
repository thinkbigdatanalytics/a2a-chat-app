import ast
import json
import time

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from db import add_toolset, get_toolsets, update_toolset, delete_toolset, \
    add_agent, update_agent, get_agents, delete_agent, get_toolsets_for_agent, get_session, \
    AgentConfig, save_config_to_db

st.set_page_config(page_title="Toolset + Agent Manager", page_icon="", layout="wide")
st.title("Toolset Manager")


tab1, tab2, tab3, tab4, tab5 = st.tabs(
    ["Add Toolset", "View Toolsets", "Add Agent", "View Agents", "Agent Configuration"]
)

with open("pages/config.json", "r") as f:
    config = json.load(f)

COMMAND_TYPES = config.get("command_types", [])
agent_name = config.get("AGENT_CONFIG", [])
google_model = config.get("google_model", [])
openai_model = config.get("openai_model", [])
anthropic_model = config.get("anthropic_model", [])
mistral_model = config.get("mistral_model", [])
local_model = config.get("local_model", [])
azure_ai = config.get("azure_ai", [])

import streamlit as st
import json
import ast

# Presets for common MCP servers
MCP_SERVER_ENV_PRESETS = {
    "github": ["GITHUB_PERSONAL_ACCESS_TOKEN"],
    "snowflake": ["SNOWFLAKE_ACCOUNT", "SNOWFLAKE_USER", "SNOWFLAKE_PASSWORD",
                  "SNOWFLAKE_DATABASE", "SNOWFLAKE_SCHEMA", "SNOWFLAKE_WAREHOUSE"],
    "postgres": ["PGHOST", "PGUSER", "PGPASSWORD", "PGDATABASE", "PGPORT"],
    "slack": ["SLACK_BOT_TOKEN", "SLACK_APP_TOKEN"],
    "jira": ["JIRA_URL", "JIRA_USER", "JIRA_API_TOKEN"],
    "s3": ["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION", "S3_BUCKET"],
    "gcs": ["GOOGLE_APPLICATION_CREDENTIALS", "GCS_BUCKET"],
    "azure_blob": ["AZURE_STORAGE_ACCOUNT", "AZURE_STORAGE_KEY", "AZURE_CONTAINER"],
    "mysql": ["MYSQL_HOST", "MYSQL_USER", "MYSQL_PASSWORD", "MYSQL_DATABASE", "MYSQL_PORT"],
    "redis": ["REDIS_HOST", "REDIS_PORT", "REDIS_PASSWORD"],
    "elasticsearch": ["ES_HOST", "ES_USERNAME", "ES_PASSWORD"],
    "kafka": ["KAFKA_BROKER", "KAFKA_USERNAME", "KAFKA_PASSWORD", "KAFKA_TOPIC"]
}

with tab1:
    st.subheader("Add New Toolset")

    # Basic Toolset Info
    name = st.text_input("Toolset Name (e.g., github, snowflake)")
    command = st.selectbox("Command Type", COMMAND_TYPES)

    # Args Input
    args = st.text_input("Args", value="")
    if command == "python":
        args = st.text_input("Python File Path", value="path/to/script.py")
    elif command == "npx":
        args = st.text_input("NPX Command", value="npx my-package")
    elif command == "http":
        args = st.text_input("HTTP Endpoint", value="http://localhost:8000/api")
    elif command == "sse":
        args = st.text_input("SSE Endpoint", value="http://localhost:8000/events")

    # Optional Environment Variables
    st.markdown("### Optional Environment Variables")
    st.caption("Set required keys for the server, e.g., GitHub token, Snowflake creds.")

    # Link to MCP servers README for reference
    st.markdown(
        "[View MCP Servers Docs](https://github.com/modelcontextprotocol/servers?tab=readme-ov-file) 🔗"
    )

    env_dict = {}
    if name.lower() in MCP_SERVER_ENV_PRESETS:
        for key in MCP_SERVER_ENV_PRESETS[name.lower()]:
            value = st.text_input(
                key,
                type="password" if "PASS" in key or "TOKEN" in key else "default",
                help=f"Set {key} for the server"
            )
            if value:
                env_dict[key] = value
    else:
        # Freeform env input
        env_input = st.text_area(
            "Custom Env Vars (optional, one per line KEY=VALUE)",
            height=120,
            placeholder="KEY=VALUE"
        )
        for line in env_input.strip().splitlines():
            if "=" in line:
                k, v = line.split("=", 1)
                env_dict[k.strip()] = v.strip()

    if st.button("Save Toolset"):
        if name and command and args:
            try:
                add_toolset(name=name, command=command, args=args, env=env_dict)
                st.success(f"Toolset '{name}' saved to DB")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please fill all fields")


def parse_args(value):
    if isinstance(value, str):
        try:
            return ast.literal_eval(value)
        except:
            return value
    return value


with tab2:
    st.subheader("Manage Toolsets")

    grid_placeholder = st.empty()

    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None

    def fetch_toolsets_df():
        toolsets = get_toolsets()
        if not toolsets:
            return pd.DataFrame()
        return pd.DataFrame([{
            "ID": t.id,
            "Name": t.name,
            "Command": t.command,
            "Args": t.args,
            "Env": t.env or "{}"
        } for t in toolsets])

    def refresh_grid():
        df_toolsets = fetch_toolsets_df()
        grid_placeholder.data_editor(
            df_toolsets, use_container_width=True,
            key=f"grid_{int(time.time() * 1000)}"
        )
        return df_toolsets

    df_toolsets = refresh_grid()

    if not df_toolsets.empty:
        df_toolsets["ID"] = df_toolsets["ID"].astype(int)

        if st.session_state.selected_id is None:
            index = 0
        else:
            index = int(df_toolsets.index[df_toolsets["ID"] == int(st.session_state.selected_id)][0])

        selected_id = st.selectbox(
            "Select a Toolset",
            options=df_toolsets["ID"].tolist(),
            index=index,
            format_func=lambda x: df_toolsets[df_toolsets["ID"] == int(x)]["Name"].values[0]
        )

        st.session_state.selected_id = int(selected_id)

        selected_tool = df_toolsets[df_toolsets["ID"] == selected_id].iloc[0]

        new_name = st.text_input("Name", value=selected_tool["Name"])
        new_command = st.text_input("Command", value=selected_tool["Command"])
        new_args = st.text_area("Args (list format)", value=str(selected_tool["Args"]))

        st.markdown("### Environment Variables (JSON format)")
        try:
            env_dict = json.loads(selected_tool["Env"])
        except:
            env_dict = {}
        new_env = st.text_area("Env JSON", value=json.dumps(env_dict, indent=2), height=150)

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Toolset", key=f"update_{selected_id}"):
                # Parse args
                try:
                    new_args_val = ast.literal_eval(new_args)
                except:
                    new_args_val = new_args

                try:
                    new_env_val = json.loads(new_env)
                except:
                    new_env_val = env_dict

                update_toolset(selected_id, new_name, new_command, new_args_val, new_env_val)
                st.success(f"Toolset '{new_name}' updated successfully!")

                st.session_state.selected_id = None
                df_toolsets = refresh_grid()

        with col2:
            if st.button("Delete Toolset", key=f"delete_{selected_id}"):
                delete_toolset(selected_id)
                st.success(f"Toolset '{selected_tool['Name']}' deleted successfully!")

                st.session_state.selected_id = None
                df_toolsets = refresh_grid()

with tab3:
    st.subheader("Add New Agent")
    all_toolsets = get_toolsets()
    toolset_options = {ts.name: ts.id for ts in all_toolsets}

    name = st.text_input("Agent Name")
    provider = st.selectbox("Select Agent Provider", agent_name)

    if provider == "Google":
        model = st.selectbox("Model", google_model)
    elif provider == "OpenAI":
        model = st.selectbox("Model", openai_model)
    elif provider == "Anthropic":
        model = st.selectbox("Model", anthropic_model)
    elif provider == "Mistral":
        model = st.selectbox("Model", mistral_model)
    elif provider == "Local":
        model = st.selectbox("Model", local_model)
    else:
        model = None

    if provider == "Azure_OPENAI":
        api_key = st.text_input("Azure API Key", type="password")
        endpoint = st.text_input("Azure Endpoint (e.g. https://xxxx.openai.azure.com/)")
        version = st.text_input("API Version", value="2024-12-01-preview")
        deployment = st.text_input("Deployment", value="ds-gpt-4o-mini")
        deployment_name = st.text_input("Deployment Name", value="ds-gpt-4o-mini")

    else:
        api_key = st.text_input("API Key", type="password")
        api_config = {"api_key": api_key}

    instruction = st.text_area("Instruction", height=100)
    selected_names = st.multiselect("Select Toolsets", list(toolset_options.keys()))

    if st.button("Save Agent"):
        if name and provider  and instruction:
            try:
                add_agent(
                    name=name,
                    provider=provider,
                    model=deployment,
                    instruction=instruction,
                    api_key=api_key,
                    AZURE_OPENAI_API_VERSION=version,
                    AZURE_OPENAI_ENDPOINT=endpoint,
                    AZURE_OPENAI_DEPLOYMENT=deployment,
                    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=deployment_name,
                    toolset_ids=[toolset_options[n] for n in selected_names]
                )
                st.success(f"Agent '{name}' ({provider}, {model}) saved successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please fill all fields")

with tab4:
    st.subheader("Manage Agents")

    # Placeholder for the grid
    grid_placeholder = st.empty()

    # Initialize session state for selected agent
    if "selected_agent_id" not in st.session_state:
        st.session_state.selected_agent_id = None

    # Function to fetch latest agents
    def fetch_agents_df():
        agents = get_agents()
        if not agents:
            return pd.DataFrame()
        return pd.DataFrame([{
            "ID": a.id,
            "Name": a.name,
            "Provider": a.provider,
            "Model": a.model,
            "Instruction": a.instruction,
            "API Key": a.api_key or "",
            "Endpoint": a.AZURE_OPENAI_ENDPOINT or "",
            "Version": a.AZURE_OPENAI_API_VERSION or "",
            "Deployment": a.AZURE_OPENAI_DEPLOYMENT or "",
            "Chat Deployment": a.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME or ""
        } for a in agents])

    def refresh_agents_grid():
        df_agents = fetch_agents_df()
        grid_placeholder.data_editor(df_agents, use_container_width=True, key=f"agent_grid_{int(time.time() * 1000)}")
        return df_agents

    df_agents = refresh_agents_grid()

    if not df_agents.empty:
        df_agents["ID"] = df_agents["ID"].astype(int)

        if st.session_state.selected_agent_id is None:
            index = 0
        else:
            index = int(df_agents.index[df_agents["ID"] == int(st.session_state.selected_agent_id)][0])

        selected_id = st.selectbox(
            "Select an Agent",
            options=df_agents["ID"].tolist(),
            index=index,
            format_func=lambda x: df_agents[df_agents["ID"] == int(x)]["Name"].values[0]
        )

        st.session_state.selected_agent_id = int(selected_id)

        selected_agent = df_agents[df_agents["ID"] == selected_id].iloc[0]

        # Editable fields for agent update
        # Editable fields for agent update
        new_name = st.text_input("Name", value=selected_agent["Name"], key=f"name_{selected_id}")
        new_provider = st.text_input("Provider", value=selected_agent["Provider"], key=f"provider_{selected_id}")
        new_model = st.text_input("Model", value=selected_agent["Model"], key=f"model_{selected_id}")
        new_instruction = st.text_area("Instruction", value=selected_agent["Instruction"],
                                       key=f"instruction_{selected_id}")
        new_api_key = st.text_input("API Key", value=selected_agent["API Key"], key=f"apikey_{selected_id}")
        new_endpoint = st.text_input("Endpoint", value=selected_agent["Endpoint"], key=f"endpoint_{selected_id}")
        new_version = st.text_input("API Version", value=selected_agent["Version"], key=f"version_{selected_id}")
        new_deployment = st.text_input("Deployment", value=selected_agent["Deployment"],
                                       key=f"deployment_{selected_id}")
        new_chat_deployment = st.text_input("Chat Deployment", value=selected_agent["Chat Deployment"],
                                            key=f"chatdeployment_{selected_id}")

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Agent", key=f"update_{selected_id}"):
                update_agent(
                    agent_id=selected_id,
                    name=new_name,
                    provider=new_provider,
                    model=new_model,
                    instruction=new_instruction,
                    api_key=new_api_key,
                    endpoint=new_endpoint,
                    version=new_version,
                    deployment=new_deployment,
                    chat_deployment=new_chat_deployment
                )
                st.success(f"Agent '{new_name}' updated successfully!")

                st.session_state.selected_agent_id = None
                df_agents = refresh_agents_grid()

        with col2:
            if st.button("Delete Agent", key=f"delete_{selected_id}"):
                delete_agent(selected_id)
                st.success(f"Agent '{selected_agent['Name']}' deleted successfully!")

                st.session_state.selected_agent_id = None
                df_agents = refresh_agents_grid()

    else:
        st.info("No agents found. Add one in 'Add Agent' tab.")



with tab5:
    st.subheader("Setup Agent Configuration")

    agent_providers = ["Google", "Azure_OPENAI", "OpenAI", "Anthropic", "Mistral", "Local"]
    selected_provider = st.selectbox("Select Main Agent Provider", agent_providers)

    # Default values
    model, api_key, endpoint, version, deployment, instruction = None, None, None, None, None, None

    # Provider specific fields
    if selected_provider == "Azure_OPENAI":
        api_key = st.text_input("Azure API Key", type="password")
        endpoint = st.text_input("Azure Endpoint", value="https://xxxx.openai.azure.com/")
        version = st.text_input("API Version", value="2024-12-01-preview")
        deployment = st.text_input("Deployment", value="ds-gpt-4o-mini")
        model = deployment
    elif selected_provider == "Google":
        api_key = st.text_input("Google API Key", type="password")
        model = st.selectbox("Model", ["gemini-2.5-pro", "gemini-1.5-flash"])
    elif selected_provider == "OpenAI":
        api_key = st.text_input("OpenAI API Key", type="password")
        model = st.selectbox("Model", ["gpt-4o-mini", "gpt-4-turbo"])
    elif selected_provider == "Anthropic":
        api_key = st.text_input("Anthropic API Key", type="password")
        model = st.selectbox("Model", ["claude-3-sonnet", "claude-3-haiku"])
    elif selected_provider == "Mistral":
        api_key = st.text_input("Mistral API Key", type="password")
        model = st.selectbox("Model", ["mistral-large", "mixtral-8x7b"])
    elif selected_provider == "Local":
        model = st.text_input("Local Model Name", "llama3")

    # 🔹 Instruction field for the agent
    instruction = st.text_area(
        "Agent Instruction",
        value="You are an intelligent assistant. Answer clearly and concisely."
    )

    apply_scope = st.radio(
        "Apply configuration to:",
        ["Only Main Agent", "Only Sub Agents", "All Agents"]
    )

    if st.button("💾 Save Configuration"):
        if not model or (not api_key and selected_provider != "Local"):
            st.error("Please provide required values.")
        else:
            with get_session() as session:
                save_config_to_db(
                    session=session,
                    agent_id=1,
                    provider=selected_provider,
                    model=model,
                    api_key=api_key,
                    endpoint=endpoint,
                    version=version,
                    deployment=deployment,
                    scope=apply_scope,
                    instruction=instruction,  # 🔹 pass to DB
                )
            st.success(f"Configuration saved for {selected_provider} ({apply_scope}).")

    st.subheader("Current Agent Configurations")

    with get_session() as session:
        configs = session.query(AgentConfig).all()
        if configs:
            config_data = [
                {
                    "Agent ID": c.agent_id,
                    "Provider": c.provider,
                    "Model": c.model,
                    "API Key": "••••••" if c.api_key else None,
                    "Endpoint": c.AZURE_OPENAI_ENDPOINT,
                    "Version": c.AZURE_OPENAI_API_VERSION,
                    "Deployment": c.AZURE_OPENAI_DEPLOYMENT,
                    "Scope": c.scope,
                    "Instruction": c.instruction[:50] + "..." if c.instruction else None,  # preview
                }
                for c in configs
            ]
            st.table(config_data)
        else:
            st.info("No configurations found.")


