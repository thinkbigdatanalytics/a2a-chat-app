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
    # api_config = Column(Js)

    toolsets = relationship("AgentToolsetModel", back_populates="agent")


class ToolsetModel(Base):
    __tablename__ = "toolsets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    command = Column(String, nullable=False)
    args = Column(Text)

    agents = relationship("AgentToolsetModel", back_populates="toolset")


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
            session.query(ToolsetModel.name, ToolsetModel.command, ToolsetModel.args)
            .join(AgentToolsetModel, ToolsetModel.id == AgentToolsetModel.toolset_id)
            .filter(AgentToolsetModel.agent_id == agent_id)
            .all()
        )
        return tools


def add_toolset(name, command, args):
    with get_session() as session:
        toolset = ToolsetModel(name=name, command=command, args=args)
        session.add(toolset)
        session.commit()


def get_toolsets():
    with get_session() as session:
        return session.query(ToolsetModel).all()


def update_toolset(toolset_id, name, command, args):
    with get_session() as session:
        toolset = session.query(ToolsetModel).filter_by(id=toolset_id).first()
        if toolset:
            toolset.name = name
            toolset.command = command
            toolset.args = args
            session.commit()


def delete_toolset(toolset_id):
    with get_session() as session:
        toolset = session.query(ToolsetModel).filter_by(id=toolset_id).first()
        if toolset:
            session.delete(toolset)
            session.commit()


def add_agent(name, provider, model, instruction,api_config = None, api_key=None, toolset_ids=None):
    with get_session() as session:
        agent = Agents(name=name, provider=provider, model=model, instruction=instruction, api_key=api_key)
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


def update_agent(agent_id, name, provider, model, instruction, api_key=None):
    with get_session() as session:
        agent = session.query(Agents).filter_by(id=agent_id).first()
        if agent:
            agent.name = name
            agent.provider = provider
            agent.model = model
            agent.instruction = instruction
            agent.api_key = api_key
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
