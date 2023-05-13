import json
import logging
import math
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler

from flask import Response, Flask, request

app = Flask(__name__)

# Configure the logger
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

# Redirect stdout and stderr to the logger
sys.stdout = handler.stream
sys.stderr = handler.stream

# dictionary to store parking lot data, key = ticket id, value = [license plate, parking lot id, entry time]
parking_lot_data = {}

@app.route('/entry', methods=['POST'])
def entry_parking():
    entry_time = datetime.now()
    plate_number = request.args.get('plateNumber')
    parking_lot = request.args.get('parkingLot')
    try:
        plate_number = int(plate_number)
        parking_lot = int(parking_lot)
    except ValueError:
        return Response(mimetype='application/json',
                        response=json.dumps({'error': 'Plate number and parking lot id must be integers'}),
                        status=400)

    ticket_id = calculate_unique_ticket_id(entry_time, plate_number)

    # store entry data in dictionary
    parking_lot_data[ticket_id] = [plate_number, parking_lot, entry_time.strftime('%s')]

    return Response(mimetype='application/json',
                    response=json.dumps({'ticketId': ticket_id}),
                    status=200)


def calculate_unique_ticket_id(datetime, plate_number):
    return str(plate_number) + '.' + datetime.strftime('%s')


@app.route('/exit', methods=['POST'])
def exit_parking():
    ticket_id = request.args.get('ticketId')

    car_data = parking_lot_data.get(ticket_id)

    if 'Item' not in car_data.keys():
        return Response(mimetype='application/json',
                        response=json.dumps({'error': 'Invalid ticket id'}),
                        status=400)

    plate_number, parking_lot, entry_time = car_data

    # calculate parked time in minutes
    parked_time_minutes = int((datetime.now() - entry_time).total_seconds() / 60)

    # calculate charge based on parked time (rounded up to nearest 15 minutes)
    charge = math.ceil(parked_time_minutes / 15) * 2.5

    response_body = {'license_plate': plate_number,
                     'parked_time': parked_time_minutes,
                     'parking_lot': parking_lot,
                     'charge': charge}

    return Response(mimetype='application/json',
                    response=json.dumps(response_body),
                    status=200)


if __name__ == '__main__':
    app.run()
