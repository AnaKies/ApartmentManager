import os

from sqlalchemy import create_engine, Column, Float, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker

# Define a path to the database
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
DB_PATH = os.path.join(BASE_DIR, "data", "log_ai_history.db")

# Create a database connection
log_engine = create_engine(f'sqlite:///{DB_PATH}', echo=True)

# Create a database session (performs CRUD operations with ORM objects)
Session = sessionmaker(bind=log_engine) # returns Fabric

# Define the data table class's parent class
Log_Base = declarative_base()

class Log(Log_Base):
    __tablename__ = "log_conversation_history"
    id_log = Column(Integer, primary_key=True)
    user_question = Column(String)
    ai_answer = Column(String)

    def __repr__(self):
        return (f"User question: {self.user_question}, "
                f"AI answer: {self.ai_answer}")