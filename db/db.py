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
class Lot(Base):
    __tablename__ = 'lots'
    id              = Column(Integer, primary_key=True)
    title           = Column(String, nullable=False)
    status          = Column(String, nullable=False)
    start_price     = Column(Integer, nullable=False)
    sold_price      = Column(Integer)
    created_at      = Column(DateTime, default=datetime.utcnow)
    starting_time   = Column(DateTime)
    ending_time     = Column(DateTime)
 
class Bid(Base):
    __tablename__ = 'bids'
    id              = Column(Integer, primary_key=True)
    lot_id          = Column(Integer, ForeignKey("lots.id"))
    bid             = Column(Integer)
    created_by      = Column(String)
    created_at      = Column(DateTime, default=datetime.utcnow)

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


