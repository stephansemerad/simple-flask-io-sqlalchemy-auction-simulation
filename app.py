#!/usr/bin/env python

import eventlet
eventlet.monkey_patch() # make sure to use eventlet and call eventlet.monkey_patch()
from flask import Flask, render_template, request, g, session, make_response, current_app, redirect, url_for
from flask_socketio import SocketIO, emit

app = Flask(__name__, static_url_path='/static')
app.config['SECRET_KEY'] = "secret"
socketio = SocketIO(app, async_mode='eventlet', logger=False, engineio_logger=False)

# Global Variables
# -------------------------------------------------------------------------

ending_time = ''
switch = False
is_auctioner_working = False
connected_ips = []

# DB - SQLalchemy
# -------------------------------------------------------------------------
from db.db import *

# Backgroud worker 
# -------------------------------------------------------------------------
worker_switch = True
def worker():
    global worker_switch
    unit_of_auction = 0
    while switch:
        unit_of_auction += 1
        print(unit_of_auction)
        data = {
            "table" : generate_table(),
            "current_lot" : generate_current_lot()
        }
        socketio.emit("update", data,  broadcast =True)
        eventlet.sleep(1)


def auctioneer():
    global switch
    

    while switch:
        global is_auctioner_working
        global ending_time

        is_auctioner_working = True
        
        # 1. Get lot on top of the auction which is in status waiting
        
        lot = session.query(Lot).filter_by(status='waiting').order_by(asc(Lot.id)).first()

        if lot == None:
            is_auctioner_working = False
            switch = False
            

        print(f"opening with lot  '{lot.id}' -  '{lot.status}' -  '{lot.title}'  " )

        # 2. Make the first item of the list live so people can bid

        lot.status          = 'live'
        starting_time       = datetime.now()
        ending_time         = datetime.now() + timedelta(seconds=5)
        lot.starting_time   = starting_time
        lot.ending_time     = ending_time
        session.commit()

        # 3. Wait until the time for the current lot has run out

        while datetime.now() < ending_time:
            eventlet.sleep(1)
            ending_time = ending_time
        
        # 4. Sell the Item
        print(f"seeling with lot  '{lot.id}' - '{lot.title}'  " )
        print("next item")
        print("")

        
        highest_bid = session.query(func.max(Bid.bid)).filter_by(lot_id=lot.id).scalar()
        if highest_bid == None:
            highest_bid = 0
            lot.status = 'unsold'
            session.commit()
        else:
            lot.status = 'sold'
            lot.sold_price = highest_bid
            session.commit()
        
        print('lot sold!')
        print("")

        is_auctioner_working = False
        # 5. Since we have changes the first item on the tops status
        eventlet.sleep(1)

# HTML
# -------------------------------------------------------------------------
@app.route('/')
def index(): return render_template('index.html')


# AJAX Functions
# -------------------------------------------------------------------------
@app.route('/start_auction',methods=['GET'])
def start_auction():
    # # 1. Change Status of all Lots
    lots = session.query(Lot)
    for lot in lots:
        if lot.status == 'sold':
            pass
        else:
            lot.status = 'waiting'
            session.commit()
            print('starting job')

    # 2. Settint the Switch for the Background worker True
    global switch
    switch = True

    # 3. Stating Background Task
    socketio.start_background_task(target=worker)
    socketio.start_background_task(target=auctioneer)

    # 4. Send message that Auction has Started
    socketio.emit("update", {"msg": "auction has been started"},  broadcast =True  )
    return 'auction has been started'

@app.route('/pause_auction',methods=['GET'])
def pause_auction():
    global switch
    global is_auctioner_working
    if switch == False and is_auctioner_working == True:
        socketio.emit("update", {"msg": "please let the auctioneer finish the current item"},  broadcast =True)
    else:
        switch = False
        socketio.emit("update", {"msg": "auction has been paused, current item will still be processed"},  broadcast =True)
        while is_auctioner_working:
            eventlet.sleep(1)
            socketio.emit("update", {"msg": "auto auctioneer is still working"},  broadcast =True)

        socketio.emit("update", {"msg": "auction is paused", 
                                 "table": generate_table()
                                },  broadcast =True)
        return 'auction has been paused'

@app.route('/reset_auction',methods=['GET'])
def reset_auction():
    # 2. Stop workers
    global switch
    switch = False

    # 2. Reset all the lots
    lots = session.query(Lot)
    for lot in lots:
        lot.status          = 'prebidding'
        lot.sold_price      = None
        lot.starting_time   = None
        lot.ending_time     = None
        session.commit()

    # 3. Reset all the bids
    bids = session.query(Bid)
    for bid in bids:
        session.delete(bid)
        session.commit()

    socketio.emit("update", {"msg": "auction has been reset", 
                             "table" : generate_table()
                            },  broadcast =True)
    return 'auction has been reset'

@app.route('/bid',methods=['GET'])
def bid():
    print('')
    print('bid')

    global switch 
    global ending_time

    print('switch: ', switch)
    if switch == True:
        bid_from    = request.remote_addr
        bid_amount  = request.args.get('bid_amount')

        print('bid_from', bid_from)
        print('bid_amount ', bid_amount)

        if bid_amount == None:
            return 'bid can not be empty or below the highest bid'
        else:
            if int(bid_amount) == 0:
                return 'bid can not be 0'
            else:
                lot = session.query(Lot).filter_by(status='live').first()
                if lot == None:
                    return 'currently no live item'
                else:

                    highest_bid = session.query(func.max(Bid.bid)).filter_by(lot_id=lot.id).scalar()
                    if highest_bid == None: 
                        highest_bid = lot.start_price

                    if int(bid_amount) == int(highest_bid):
                        return 'bid is equal to current price'
                    else:
                        if int(bid_amount) <= int(highest_bid):
                            return 'bid is smaller than current price'
                        else:
                            bid = Bid(lot_id = lot.id, bid=bid_amount)
                            session.add(bid)
                            session.commit()    
                            ending_time = ending_time + timedelta(seconds=2)
                            ip = request.remote_addr
                            socketio.emit("update", {   
                                                    "msg": f"{ip} has bid {bid_amount}",
                                                    "table" : generate_table(),
                                                    "current_lot": generate_current_lot(),
                                                    },  broadcast =True  )
                            return f"bid  lot: {lot.id} | {bid_amount} was accepted" 

# Socket IO Functions
# -------------------------------------------------------------------------
@socketio.on('connect')
def connect():
    # 1. Confirmation that someone has connected
    ip = request.remote_addr

    global connected_ips
    if ip not in connected_ips:
        connected_ips.append(ip)
    
    print('connect')
    socketio.emit("update", {
                                "msg": "connection accepted from "+ ip,
                                "table": generate_table(),
                                "current_lot": generate_current_lot(),

                            }, broadcast =False)


# Helper HTML Rendering Functions
# -------------------------------------------------------------------------
def generate_table():
    html = ''
    html += '''
    <table style="font-size:12px" class="table">
    <thead>
        <tr>
            <th scope="col">id</th>
            <th scope="col">title</th>
            <th scope="col">status</th>
            <th scope="col">start_price</th>
            <th scope="col">sold_price</th>
            <th scope="col">starting_time</th>
            <th scope="col">ending_time</th>
            <th scope="col">highest_bid</th>

        </tr>
    </thead>
    '''
    lots = session.query(Lot)
    for lot in lots:
        highest_bid = session.query(func.max(Bid.bid)).filter_by(lot_id=lot.id).scalar()
        html += f'''
        <tr>
            <td>{str(lot.id)}</td>
            <td>{str(lot.title)}</td>
            <td class="{'text-success' if lot.status == 'live' else ''}">{str(lot.status)}</td>
            <td>{str(lot.start_price)}</td>
            <td>{str(lot.sold_price)}</td>
            <td>{str('-' if lot.starting_time == None else lot.starting_time.strftime("%H:%M:%S"))}</td>
            <td>{str('-' if lot.ending_time == None else lot.ending_time.strftime("%H:%M:%S"))}</td>
            <td>{str(highest_bid)}</td>
        </tr>
        '''
    html += '''</tbody></table>'''
    return html






def generate_current_lot():
    print('generate_current_lot')
    global connected_ips
    data = {}
    lot = session.query(Lot).filter(Lot.status=='live').first()
    print('lot ', lot)
    global ending_time

    if lot != None and ending_time != '':
        print('current_lot_id ', lot.id)
        highest_bid = session.query(func.max(Bid.bid)).filter_by(lot_id=lot.id).scalar()
        if highest_bid == None:
            highest_bid = lot.start_price

        lot_remaining_time = ending_time - datetime.now()
        lot_remaining_time = str(lot_remaining_time)[:7]
        
        # A Couple of seconds until db stores
        if lot_remaining_time == '-1 day,': lot_remaining_time = '0:00:00' 

        data =  {
            'lot_id'            : lot.id,
            'lot_title'         : lot.title,
            'lot_status'        : lot.status,
            'lot_starting_time' : lot.starting_time.strftime("%H:%M:%S"),
            'lot_ending_time'   : lot.ending_time.strftime("%H:%M:%S"),
            'lot_remaining_time': lot_remaining_time,
            'current_price'     : highest_bid,
            'current_time'      : datetime.now().strftime("%H:%M:%S"),
            'currently_viewing' : len(connected_ips)

        }
        print('current_lot_data: ', data)
        return data



if __name__ == '__main__':
    socketio.run(app, host="0.0.0.0", port=80, debug=True)
