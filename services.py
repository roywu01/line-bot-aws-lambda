from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os

# mysql+pymysql://account:password@exapmle.rds.amazonaws.com:3306/stock?charset=utf8
engine = create_engine(os.environ.get('connection_string'))
session = sessionmaker(bind=engine)
SqlBase = declarative_base()
Session = session()
