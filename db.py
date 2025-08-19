from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Text
from sqlalchemy.orm import sessionmaker, relationship, declarative_base

DB_URL = "sqlite:///agents.db"

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()

class Agent(Base):
    __tablename__ = "agents"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    instruction = Column(String, nullable=False)
    api_key = Column(String, nullable=True)

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

    agent = relationship("Agent", back_populates="toolsets")
    toolset = relationship("ToolsetModel", back_populates="agents")


Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()


def get_all_agents():
    with get_session() as session:
        agents = session.query(Agent).all()
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
