import json
import pandas as pd
import streamlit as st
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, UniqueConstraint
from sqlalchemy.orm import declarative_base, relationship, sessionmaker


DB_URL = "sqlite:///agents.db"
engine = create_engine(DB_URL, echo=False)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Toolset(Base):
    __tablename__ = "toolsets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    command = Column(String, nullable=False)
    args = Column(String, nullable=False)

    agents = relationship("AgentToolset", back_populates="toolset")


class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)
    instruction = Column(String, nullable=False)
    api_key = Column(String, nullable=True)

    toolsets = relationship("AgentToolset", back_populates="agent")


class AgentToolset(Base):
    __tablename__ = "agent_toolsets"

    agent_id = Column(Integer, ForeignKey("agents.id"), primary_key=True)
    toolset_id = Column(Integer, ForeignKey("toolsets.id"), primary_key=True)

    agent = relationship("Agent", back_populates="toolsets")
    toolset = relationship("Toolset", back_populates="agents")


def init_db():
    Base.metadata.create_all(bind=engine)


def add_toolset(name, command, args):
    with SessionLocal() as session:
        toolset = Toolset(name=name, command=command, args=args)
        session.add(toolset)
        session.commit()


def get_toolsets():
    with SessionLocal() as session:
        return session.query(Toolset).all()


def update_toolset(toolset_id, name, command, args):
    with SessionLocal() as session:
        toolset = session.query(Toolset).filter_by(id=toolset_id).first()
        if toolset:
            toolset.name = name
            toolset.command = command
            toolset.args = args
            session.commit()


def delete_toolset(toolset_id):
    with SessionLocal() as session:
        toolset = session.query(Toolset).filter_by(id=toolset_id).first()
        if toolset:
            session.delete(toolset)
            session.commit()


def add_agent(name, model, instruction, toolset_ids=None):
    with SessionLocal() as session:
        agent = Agent(name=name, model=model, instruction=instruction)
        session.add(agent)
        session.commit()

        if toolset_ids:
            for tid in toolset_ids:
                link = AgentToolset(agent_id=agent.id, toolset_id=tid)
                session.add(link)
            session.commit()


def get_agents():
    with SessionLocal() as session:
        return session.query(Agent).all()


def update_agent(agent_id, name, model, instruction):
    with SessionLocal() as session:
        agent = session.query(Agent).filter_by(id=agent_id).first()
        if agent:
            agent.name = name
            agent.model = model
            agent.instruction = instruction
            session.commit()


def delete_agent(agent_id):
    with SessionLocal() as session:
        agent = session.query(Agent).filter_by(id=agent_id).first()
        if agent:
            session.delete(agent)
            session.commit()


def link_agent_toolsets(agent_id, toolset_ids):
    with SessionLocal() as session:
        for tid in toolset_ids:
            link = AgentToolset(agent_id=agent_id, toolset_id=tid)
            session.merge(link)
        session.commit()


def get_toolsets_for_agent(agent_id):
    with SessionLocal() as session:
        links = session.query(AgentToolset).filter_by(agent_id=agent_id).all()
        return [link.toolset.name for link in links]


st.set_page_config(page_title="Toolset + Agent Manager", page_icon="", layout="wide")
st.title("Toolset Manager")

init_db()

tab1, tab2, tab3, tab4 = st.tabs(["Add Toolset", "View Toolsets", "Add Agent", "View Agents"])

with open("pages/config.json", "r") as f:
    config = json.load(f)

COMMAND_TYPES = config.get("command_types", [])
agent_name = config.get("AGENT_CONFIG", [])
google_model = config.get("google_model", [])
openai_model = config.get("openai_model", [])
anthropic_model = config.get("anthropic_model", [])
mistral_model = config.get("mistral_model", [])
local_model = config.get("local_model", [])


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


with tab2:
    st.subheader("Manage Toolsets")
    toolsets = get_toolsets()
    if toolsets:
        df_toolsets = pd.DataFrame([{
            "ID": t.id, "Name": t.name, "Command": t.command, "Args": t.args
        } for t in toolsets])
        edited_df = st.data_editor(df_toolsets, use_container_width=True, num_rows="dynamic")

        if not edited_df.equals(df_toolsets):
            for i in range(len(edited_df)):
                row = edited_df.iloc[i]
                orig_row = df_toolsets.iloc[i]
                if not row.equals(orig_row):
                    update_toolset(row["ID"], row["Name"], row["Command"], row["Args"])
            st.success("Toolsets updated successfully!")

        delete_id = st.selectbox("Select Toolset ID to delete", df_toolsets["ID"])
        if st.button("Delete Toolset"):
            delete_toolset(delete_id)
            st.warning(f"Toolset ID {delete_id} deleted.")
            st.experimental_rerun()
    else:
        st.info("No toolsets found. Add one in 'Add Toolset' tab.")


with tab3:
    st.subheader("Add New Agent")
    all_toolsets = get_toolsets()
    toolset_options = {ts.name: ts.id for ts in all_toolsets}

    name = st.text_input("Agent Name")
    select = st.selectbox("Select Agent Provider", agent_name)

    if select == "Google":
        model = st.selectbox("Model", google_model)
    elif select == "OpenAI":
        model = st.selectbox("Model", openai_model)
    elif select == "Anthropic":
        model = st.selectbox("Model", anthropic_model)
    elif select == "Mistral":
        model = st.selectbox("Model", mistral_model)
    elif select == "Local":
        model = st.selectbox("Model", local_model)
    else:
        model = None

    api_key = st.text_input("API Key")
    instruction = st.text_area("Instruction", height=100)
    selected_names = st.multiselect("Select Toolsets", list(toolset_options.keys()))

    if st.button("Save Agent"):
        if name and select and model and instruction:
            try:
                add_agent(name, model, instruction, [toolset_options[n] for n in selected_names])
                st.success(f"Agent '{name}' ({select}, {model}) saved successfully!")
            except Exception as e:
                st.error(f"Error: {e}")
        else:
            st.error("Please fill all fields")

with tab4:
    st.subheader("Manage Agents")
    agents = get_agents()
    if agents:
        df_agents = pd.DataFrame([{
            "ID": a.id, "Name": a.name, "Model": a.model, "Instruction": a.instruction
        } for a in agents])
        edited_df = st.data_editor(df_agents, use_container_width=True, num_rows="dynamic")

        if not edited_df.equals(df_agents):
            for i in range(len(edited_df)):
                row = edited_df.iloc[i]
                orig_row = df_agents.iloc[i]
                if not row.equals(orig_row):
                    update_agent(row["ID"], row["Name"], row["Model"], row["Instruction"])
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
