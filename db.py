import json

from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

DB_URL = "sqlite:///agents.db"

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


class Agents(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    instruction = Column(String, nullable=False)
    api_key = Column(String, nullable=True)
    AZURE_OPENAI_API_VERSION = Column(String, nullable=True)
    AZURE_OPENAI_ENDPOINT = Column(String,nullable=True)
    AZURE_OPENAI_DEPLOYMENT = Column(String, nullable=True)
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = Column(String,nullable=True)

    config = relationship("AgentConfig", back_populates="agent", uselist=False)

    toolsets = relationship("AgentToolsetModel", back_populates="agent")



class AgentConfig(Base):
    __tablename__ = "agent_config"

    id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(Integer, ForeignKey("agents.id"), nullable=False)
    provider = Column(String, nullable=True)
    model = Column(String, nullable=True)
    api_key = Column(String, nullable=True)
    scope = Column(String, nullable=True)
    AZURE_OPENAI_API_VERSION = Column(String, nullable=True)
    AZURE_OPENAI_ENDPOINT = Column(String, nullable=True)
    AZURE_OPENAI_DEPLOYMENT = Column(String, nullable=True)
    AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = Column(String, nullable=True)
    instruction = Column(String, nullable=True)

    agent = relationship("Agents", back_populates="config")
class ToolsetModel(Base):
    __tablename__ = "toolsets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    command = Column(String, nullable=False)
    args = Column(Text)
    env = Column(Text, nullable=True)

    agents = relationship("AgentToolsetModel", back_populates="toolset")

def save_config_to_db(
    session,
    agent_id,
    provider,
    model,
    api_key=None,
    endpoint=None,
    version=None,
    deployment=None,
    scope=None,
    instruction=None   # 🔹 Added
):
    from sqlalchemy.exc import SQLAlchemyError
    try:
        config = session.query(AgentConfig).filter_by(agent_id=agent_id).first()
        if not config:
            config = AgentConfig(agent_id=agent_id)
            session.add(config)

        config.api_key = api_key
        config.model = model
        config.provider = provider
        config.AZURE_OPENAI_ENDPOINT = endpoint
        config.AZURE_OPENAI_API_VERSION = version
        config.AZURE_OPENAI_DEPLOYMENT = deployment
        config.scope = scope
        config.instruction = instruction

        session.commit()
        print(f"[INFO] Config saved for agent {agent_id} (provider={provider}, model={model})")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"[ERROR] Failed to save config for agent {agent_id}: {str(e)}")

class AgentToolsetModel(Base):
    __tablename__ = "agent_toolsets"
    id = Column(Integer, primary_key=True, index=True)
    agent_id = Column(Integer, ForeignKey("agents.id"))
    toolset_id = Column(Integer, ForeignKey("toolsets.id"))

    agent = relationship("Agents", back_populates="toolsets")
    toolset = relationship("ToolsetModel", back_populates="agents")


Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


def get_all_agents():
    with get_session() as session:
        agents = session.query(Agents).all()
        return [(a.id, a.name, a.model, a.instruction) for a in agents]


def get_all_tools_by_id(agent_id):
    with get_session() as session:
        tools = (
            session.query(ToolsetModel.name, ToolsetModel.command, ToolsetModel.args,ToolsetModel.env)
            .join(AgentToolsetModel, ToolsetModel.id == AgentToolsetModel.toolset_id)
            .filter(AgentToolsetModel.agent_id == agent_id)
            .all()
        )
        return tools



def add_toolset(name, command, args, env=None):
    with get_session() as session:
        existing = session.query(ToolsetModel).filter_by(name=name).first()
        if existing:
            raise ValueError(f"Toolset with name '{name}' already exists.")

        toolset = ToolsetModel(
            name=name,
            command=command,
            args=args,
            env=json.dumps(env) if env else "{}"
        )
        session.add(toolset)
        session.commit()


def get_toolsets():
    with get_session() as session:
        return session.query(ToolsetModel).all()

def get_agent_config(agent_id: int, provider: str = None):
    with get_session() as session:
        query = session.query(AgentConfig).filter_by(agent_id=agent_id)
        # if provider:
        #     query = query.filter_by(provider=provider)
        return query.first()

def update_toolset(toolset_id, name, command, args, env=None):

    with get_session() as session:
        toolset = session.query(ToolsetModel).filter_by(id=toolset_id).first()
        if toolset:
            toolset.name = name
            toolset.command = command
            toolset.args = args
            toolset.env = json.dumps(env) if env else toolset.env  # update env if provided
            session.commit()


def delete_toolset(toolset_id):

    with get_session() as session:
        toolset = session.query(ToolsetModel).filter_by(id=toolset_id).first()
        if toolset:
            session.delete(toolset)
            session.commit()


def add_agent(name, provider, model, instruction, api_key=None,AZURE_OPENAI_API_VERSION = None ,AZURE_OPENAI_ENDPOINT=None,AZURE_OPENAI_DEPLOYMENT=None,AZURE_OPENAI_CHAT_DEPLOYMENT_NAME= None, toolset_ids=None):
    with get_session() as session:
        agent = Agents(name=name, provider=provider, model=model, instruction=instruction, api_key=api_key,AZURE_OPENAI_API_VERSION=AZURE_OPENAI_API_VERSION,AZURE_OPENAI_ENDPOINT=AZURE_OPENAI_ENDPOINT,AZURE_OPENAI_DEPLOYMENT=AZURE_OPENAI_DEPLOYMENT,AZURE_OPENAI_CHAT_DEPLOYMENT_NAME=AZURE_OPENAI_CHAT_DEPLOYMENT_NAME)
        session.add(agent)
        session.commit()

        if toolset_ids:
            for tid in toolset_ids:
                link = AgentToolsetModel(agent_id=agent.id, toolset_id=tid)
                session.add(link)
            session.commit()


def get_agents():
    with get_session() as session:
        return session.query(Agents).all()


def update_agent(
    agent_id,
    name,
    provider,
    model,
    instruction,
    api_key=None,
    endpoint=None,
    version=None,
    deployment=None,
    chat_deployment=None
):
    with get_session() as session:
        agent = session.query(Agents).filter_by(id=agent_id).first()
        if agent:
            agent.name = name
            agent.provider = provider
            agent.model = model
            agent.instruction = instruction
            agent.api_key = api_key
            agent.AZURE_OPENAI_ENDPOINT = endpoint
            agent.AZURE_OPENAI_API_VERSION = version
            agent.AZURE_OPENAI_DEPLOYMENT = deployment
            agent.AZURE_OPENAI_CHAT_DEPLOYMENT_NAME = chat_deployment

            session.commit()



def delete_agent(agent_id):
    with get_session() as session:
        agent = session.query(Agents).filter_by(id=agent_id).first()
        if agent:
            session.delete(agent)
            session.commit()


def link_agent_toolsets(agent_id, toolset_ids):
    with get_session() as session:
        for tid in toolset_ids:
            link = AgentToolsetModel(agent_id=agent_id, toolset_id=tid)
            session.merge(link)
        session.commit()


def get_toolsets_for_agent(agent_id):
    with get_session() as session:
        links = session.query(AgentToolsetModel).filter_by(agent_id=agent_id).all()
        return [link.toolset.name for link in links]
