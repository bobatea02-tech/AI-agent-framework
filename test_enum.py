
from sqlalchemy import Column, Integer, Enum, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()

class TestModel(Base):
    __tablename__ = 'test_model'
    id = Column(Integer, primary_key=True)
    status = Column(Enum('pending', 'running', 'completed', 'failed', name='workflow_status_enum', create_type=False))

try:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    print("Table created successfully")
    
    Session = sessionmaker(bind=engine)
    session = Session()
    m = TestModel(status='pending')
    session.add(m)
    session.commit()
    print("Insert successful")
except Exception as e:
    import traceback
    traceback.print_exc()
