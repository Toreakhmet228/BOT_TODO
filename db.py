from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from config import configs

engine=create_engine(url=configs.DATABASE_URL)
Sessionlocal=sessionmaker(bind=engine)

Base=declarative_base( )

def get_db():
    db=Sessionlocal()
    try:
        yield db
    finally:
        db.close()