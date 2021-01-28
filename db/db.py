import sqlalchemy
from datetime import datetime, timedelta
from sqlalchemy import create_engine, ForeignKey, Column, Integer, String, DateTime, func
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import or_, and_
from sqlalchemy import desc, asc    

engine  = create_engine('sqlite:///db.sqlite3', echo=False)
tables  = engine.table_names()
Session = sessionmaker(bind=engine)
session = Session()

Base = declarative_base()

from sqlalchemy import Column, Integer, String

class User(Base):
    __tablename__ = 'users'
    id              = Column(Integer, primary_key=True)
    # user_data
    first_name      = Column(String, nullable=False)
    second_name     = Column(String, nullable=False)
    email           = Column(String, nullable=False)
    tel             = Column(String, nullable=False)
    address         = Column(String, nullable=False)
    city            = Column(String, nullable=False)
    country         = Column(String, nullable=False)
    company_name    = Column(String)
    tax_number      = Column(String)
    consignor       = Column(Boolean, default=False)
    admin           = Column(Boolean, default=False)
    black_listed    = Column(Boolean, default=False)

    # meta_data
    password        = Column(String)
    login_attempts  = Column(String)
    locked_until    = Column(DateTime)
    last_login      = Column(DateTime)

    updated_by      = Column(Integer)
    updated_at      = Column(DateTime)
    created_at      = Column(DateTime, default=datetime.utcnow)

class Auction(Base):
    __tablename__ = 'auctions'
    id              = Column(Integer, primary_key=True)
    title           = Column(String, nullable=False)
    status          = Column(String, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)
    starting_time   = Column(DateTime)
    ending_time     = Column(DateTime)

class Auction_Status(Base):
    __tablename__ = 'auction_status'
    status          = Column(String, nullable=False)

class Lot(Base):
    __tablename__ = 'lots'
    id              = Column(Integer, primary_key=True)
    title           = Column(String, nullable=False)
    description     = Column(String, nullable=False)
    status          = Column(String, nullable=False)
    country_code    = Column(String, nullable=False)
    category_id     = Column(String, nullable=False)
    start_price     = Column(Integer, nullable=False)
    reserve_price   = Column(Integer)
    sold_price      = Column(Integer)
    starting_time   = Column(DateTime)
    ending_time     = Column(DateTime)
    updated_by      = Column(DateTime, default=datetime.utcnow)
    updated_at      = Column(DateTime, default=datetime.utcnow)
    created_by      = Column(DateTime, default=datetime.utcnow)
    created_at      = Column(DateTime, default=datetime.utcnow)

class Lot_Status(Base):
    __tablename__ = 'lot_status'
    status          = Column(String, nullable=False)
 
 class Images(Base):
    __tablename__ = 'images'
    id              = Column(Integer, primary_key=True)
    lot_id          = Column(Integer)
    img             = Column(String, nullable=False)
    uploaded_by     = Column(String, nullable=False)
    uploaded_at     = Column(String, nullable=False)

 class Countries(Base):
    __tablename__ = 'images'
    id            = Column(String, primary_key=True)
    name          = Column(String, nullable=False)

 class Categories(Base):
    __tablename__ = 'images'
    id            = Column(String, primary_key=True)
    name          = Column(String, nullable=False)

class Bid(Base):
    __tablename__ = 'bids'
    id              = Column(Integer, primary_key=True)
    lot_id          = Column(Integer, ForeignKey("lots.id"))
    bid             = Column(Integer)
    user_id         = Column(Integer)
    created_by      = Column(String)
    created_at      = Column(DateTime, default=datetime.utcnow)

class Increments(Base):
    __tablename__ = 'increments'
    amount          = Column(Integer)
    increments      = Column(Integer)




if tables != ['bids', 'lots']:
    Base.metadata.create_all(engine)


# lots = session.query(Lot)
# for lot in lots:
#     print(lot.id)
#     session.delete(lot)
#     session.commit()

# for i in range(16):
#     i = i + 1
#     lot = Lot(title = 'lot_'+str(i), status='prebidding', start_price = 5)
#     session.add(lot)
#     session.commit()




# lot = session.query(Lot).filter_by(id=1).first()
# lot.status = 'live'
# session.commit()




# print('LOT: ', lot.id)


