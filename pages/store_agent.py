import ast
import json
import time

import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from db import get_all_agents, get_all_tools_by_id, add_toolset, get_toolsets, update_toolset, delete_toolset, \
    add_agent, update_agent, get_agents, delete_agent, get_toolsets_for_agent

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


with tab1:
    st.subheader("Add New Toolset")
    name = st.text_input("Toolset Name (e.g., mcp.add)")
    command = st.selectbox("Command Type", COMMAND_TYPES)

    args = st.text_input("Args", value="")
    if command == "python":
        args = st.text_input("Python File Path", value="path/to/script.py")
    elif command == "npx":
        args = st.text_input("NPX Command", value="npx my-package")
    elif command == "http":
        args = st.text_input("HTTP Endpoint", value="http://localhost:8000/api")
    elif command == "sse":
        args = st.text_input("SSE Endpoint", value="http://localhost:8000/events")

    if st.button("Save Toolset"):
        if name and command and args:
            try:
                add_toolset(name, command, args)
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

    # Placeholder for the grid
    grid_placeholder = st.empty()

    # Initialize session state for selected tool
    if "selected_id" not in st.session_state:
        st.session_state.selected_id = None

    # Function to fetch latest toolsets
    def fetch_toolsets_df():
        toolsets = get_toolsets()
        if not toolsets:
            return pd.DataFrame()
        return pd.DataFrame([{
            "ID": t.id, "Name": t.name, "Command": t.command, "Args": t.args
        } for t in toolsets])

    # Function to refresh grid in the placeholder
    def refresh_grid():
        df_toolsets = fetch_toolsets_df()
        # Add a unique key using timestamp
        grid_placeholder.data_editor(df_toolsets, use_container_width=True, key=f"grid_{int(time.time() * 1000)}")
        return df_toolsets

    # Initial load
    df_toolsets = refresh_grid()

    if not df_toolsets.empty:
        # Select a toolset (use session_state to reset selection if needed)
        df_toolsets["ID"] = df_toolsets["ID"].astype(int)

        # Compute index safely
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

        # Store as Python int in session_state
        st.session_state.selected_id = int(selected_id)

        selected_tool = df_toolsets[df_toolsets["ID"] == selected_id].iloc[0]

        # Editable fields
        new_name = st.text_input("Name", value=selected_tool["Name"])
        new_command = st.text_input("Command", value=selected_tool["Command"])
        new_args = st.text_area("Args (list format)", value=str(selected_tool["Args"]))

        col1, col2 = st.columns(2)
        with col1:
            if st.button("Update Toolset", key=f"update_{selected_id}"):
                try:
                    new_args_val = ast.literal_eval(new_args)
                except:
                    new_args_val = new_args

                update_toolset(selected_id, new_name, new_command, new_args_val)
                st.success(f"Toolset '{new_name}' updated successfully!")

                # Reset selected_id to force reload
                st.session_state.selected_id = None
                df_toolsets = refresh_grid()

        with col2:
            if st.button("Delete Toolset", key=f"delete_{selected_id}"):
                delete_toolset(selected_id)
                st.success(f"Toolset '{selected_tool['Name']}' deleted successfully!")

                # Reset selected_id to force reload
                st.session_state.selected_id = None
                df_toolsets = refresh_grid()
with tab3:
    st.subheader("Add New Agent")
    all_toolsets = get_toolsets()
    toolset_options = {ts.name: ts.id for ts in all_toolsets}

    name = st.text_input("Agent Name")
    provider = st.selectbox("Select Agent Provider", agent_name)

    # Model selection based on provider
    if provider == "Google":
        model = st.selectbox("Model", google_model)
    elif provider == "Azure_OPENAI":
        model = st.selectbox("Model", azure_ai)
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
        deployment = st.text_input("Deployment Name", value="ds-gpt-4o-mini")

        api_config = {
            "api_key": api_key,
            "endpoint": endpoint,
            "version": version,
            "deployment": deployment,
        }
    else:
        api_key = st.text_input("API Key", type="password")
        api_config = {"api_key": api_key}

    instruction = st.text_area("Instruction", height=100)
    selected_names = st.multiselect("Select Toolsets", list(toolset_options.keys()))

    if st.button("Save Agent"):
        if name and provider and model and instruction:
            try:
                import json
                add_agent(
                    name,
                    provider,
                    model,
                    instruction,
                    json.dumps(api_config),
                    None,
                    [toolset_options[n] for n in selected_names]
                )
                st.success(f"Agent '{name}' ({provider}, {model}) saved successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please fill all fields")

with tab4:
    st.subheader("Manage Agents")
    agents = get_agents()
    if agents:
        df_agents = pd.DataFrame([{
            "ID": a.id,
            "Name": a.name,
            "Provider": a.provider,
            "Model": a.model,
            "Instruction": a.instruction,
            "API Key": a.api_key if a.api_key else ""
        } for a in agents])

        edited_df = st.data_editor(df_agents, use_container_width=True, num_rows="dynamic")

        if not edited_df.equals(df_agents):
            for i in range(len(edited_df)):
                row = edited_df.iloc[i]
                orig_row = df_agents.iloc[i]
                if not row.equals(orig_row):
                    update_agent(
                        agent_id=row["ID"],
                        name=row["Name"],
                        provider=row["Provider"],
                        model=row["Model"],
                        instruction=row["Instruction"],
                        api_key=row["API Key"]
                    )
            st.success("Agents updated successfully!")

        delete_id = st.selectbox("Select Agent ID to delete", df_agents["ID"])
        if st.button("Delete Agent"):
            delete_agent(delete_id)
            st.warning(f"Agent ID {delete_id} deleted.")
            st.experimental_rerun()

        agent_toolsets_data = []
        for a in agents:
            ts_names = get_toolsets_for_agent(a.id)
            agent_toolsets_data.append({
                "Agent ID": a.id,
                "Agent Name": a.name,
                "Toolsets": ", ".join(ts_names) if ts_names else "None"
            })
        df_agent_toolsets = pd.DataFrame(agent_toolsets_data)
        st.markdown("### Agent → Toolsets Mapping")
        st.dataframe(df_agent_toolsets, use_container_width=True)
    else:
        st.info("No agents found. Add one in 'Add Agent' tab.")

with tab5:
    st.subheader("Setup Agent Configuration")

    # Step 1: Select main agent
    agent_providers = ["Google", "Azure_OPENAI", "OpenAI", "Anthropic", "Mistral", "Local"]
    selected_provider = st.selectbox("Select Main Agent", agent_providers)

    # Step 2: Enter API Key
    api_key = st.text_input(f"Enter API Key for {selected_provider}", type="password")

    # Step 3: Choose scope (for all agents OR only this one)
    apply_scope = st.radio(
        "Do you want to set the API key for:",
        ["Only this agent", "All agents"]
    )


    def update_api_key_for_agent(provider, api_key):
        agents = get_agents()
        for a in agents:
            if a.provider == provider:
                update_agent(
                    agent_id=a.id,
                    name=a.name,
                    provider=a.provider,
                    model=a.model,
                    instruction=a.instruction,
                    api_key=api_key
                )


    if st.button("Save Configuration"):
        if not api_key.strip():
            st.error("API Key cannot be empty.")
        else:
            if apply_scope == "Only this agent":
                # Save API key only for the selected agent
                update_api_key_for_agent(selected_provider, api_key)
                st.success(f"API Key set for {selected_provider} only.")
            else:
                # Save API key for all agents
                for provider in agent_providers:
                    update_api_key_for_agent(provider, api_key)
                st.success("API Key set for all agents successfully!")



