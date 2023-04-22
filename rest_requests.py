from flask import Flask, request, jsonify
import datetime

app = Flask(__name__)

# dictionary to store parking lot data, key = ticket id, value = [license plate, parking lot id, entry time]
parking_lot_data = {}


@app.route('/entry', methods=['POST'])
def entry_parking():
    # POST /entry?plate=123-123-123&amp;parkingLot=382
    datetime_now = datetime.datetime.now()
    plate = request.args.get('plate')
    parking_lot = request.args.get('parkingLot')

    # generate ticket id by concatenating plate and current timestamp
    ticket_id = plate + str(datetime_now.timestamp())

    # store entry data in dictionary
    parking_lot_data[ticket_id] = [plate, parking_lot, datetime_now]

    # todo : send here to the server
    return jsonify({'ticketId': ticket_id})


@app.route('/exit', methods=['POST'])
def exit_parking():
    # POST /exit?ticketId=1234
    ticket_id = request.args.get('ticketId')

    # retrieve entry data from dictionary
    entry_data = parking_lot_data.get(ticket_id)
    if entry_data is None:
        return jsonify({'error': 'Invalid ticketId'})

    plate, parking_lot, entry_time = entry_data

    # calculate parked time in minutes
    parked_time = int((datetime.datetime.now() - entry_time).total_seconds() / 60)

    # calculate charge based on parked time (rounded up to nearest 15 minutes)
    charge = round(parked_time / 15) * 10

    # remove entry data from dictionary
    del parking_lot_data[ticket_id]

    # todo : send here to the server
    return jsonify({'licensePlate': plate, 'parkedTime': parked_time, 'parkingLot': parking_lot, 'charge': charge})


if __name__ == '__main__':
    app.run()
