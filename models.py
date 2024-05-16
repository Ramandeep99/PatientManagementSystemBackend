from database import Base
from sqlalchemy import Column, Integer, String, Boolean, Float


class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    category = Column(String)
    description = Column(String)
    is_income = Column(Boolean)
    date = Column(String)


class Patient(Base):
    __tablename__ = 'patients'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    age = Column(String)
    contact_num = Column(String)
    date_of_birth = Column(String)


class PaymentLink(Base):
    __tablename__ = "payment_links"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    payment_link = Column(String)
    amount = Column(Integer)
    doctor_name = Column(String)