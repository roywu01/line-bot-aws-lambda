# coding: utf-8
from sqlalchemy import Column, DECIMAL, Date, DateTime, String, text
from sqlalchemy.dialects.mysql import INTEGER
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()
metadata = Base.metadata


class Stock(Base):
    __tablename__ = 'stock'

    id = Column(INTEGER(11), primary_key=True)
    stock_id = Column(String(255), nullable=False)
    date = Column(Date, nullable=False)
    created_time = Column(DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP"))
    price = Column(DECIMAL(10, 2), nullable=False)

    def __init__(self, stock_id, date, price):
        self.stock_id = stock_id
        self.date = date
        self.price = price


class Tracking(Base):
    __tablename__ = 'tracking'

    stock_id = Column(String(255), primary_key=True)

    def __init__(self, stock_id):
        self.stock_id = stock_id
