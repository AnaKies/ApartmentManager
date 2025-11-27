import os

from sqlalchemy import create_engine, Column, Float, Integer, String, DateTime, func
from sqlalchemy.orm import declarative_base, sessionmaker

# Define a path to the database
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DB_PATH = os.path.join(BASE_DIR, "data", "log_conversation.db")

# Create a database connection
log_engine = create_engine(f'sqlite:///{DB_PATH}',
                           connect_args={'check_same_thread': False, "timeout": 15},
                           echo=False)

# Create a database session (performs CRUD operations with ORM objects)
Session = sessionmaker(bind=log_engine) # returns Fabric

# Define the data table class's parent class
Log_Base = declarative_base()

class Log(Log_Base):
    __tablename__ = "log_conversation"
    id_log = Column(Integer, primary_key=True, autoincrement=True)
    ai_model = Column(String)
    user_question = Column(String)
    request_type = Column(String)
    back_end_response = Column(String)
    ai_answer = Column(String)
    system_prompt_name = Column(String)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())