from enum import Enum

from flask import Response, Flask, request
import boto3
from datetime import datetime
import json
import math

app = Flask(__name__)

TABLE_NAME = 'ParkingLotDB'
dynamodb_client = boto3.resource('dynamodb', region_name='eu-central-1')
parking_lot_table = dynamodb_client.Table('ParkingLotDB')


class DynamoDbKeys(Enum):
    TICKET_ID = 'ticket_id'
    ENTRY_TIMESTAMP = 'entry_timestamp'
    PLATE_NUMBER = 'plate_number'
    PARKING_LOT = 'parking_lot'


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

    parking_lot_table.put_item(Item={DynamoDbKeys.TICKET_ID.value: ticket_id,
                                     DynamoDbKeys.ENTRY_TIMESTAMP.value: entry_time.strftime('%s'),
                                     DynamoDbKeys.PLATE_NUMBER.value: plate_number,
                                     DynamoDbKeys.PARKING_LOT.value: parking_lot})

    return Response(mimetype='application/json',
                    response=json.dumps({'ticketId': ticket_id}),
                    status=200)


def calculate_unique_ticket_id(datetime, plate_number):
    return str(plate_number) + '.' + datetime.strftime('%s')


@app.route('/exit', methods=['POST'])
def exit_parking():
    ticket_id = request.args.get('ticketId')

    car_data = parking_lot_table.get_item(Key={DynamoDbKeys.TICKET_ID.value: ticket_id})

    if 'Item' not in car_data.keys():
        return Response(mimetype='application/json',
                        response=json.dumps({'error': 'Invalid ticket id'}),
                        status=400)

    entry_time = datetime.fromtimestamp(int(car_data["Item"][DynamoDbKeys.ENTRY_TIMESTAMP.value]))
    plate_number = int(car_data["Item"][DynamoDbKeys.PLATE_NUMBER.value])
    parking_lot = int(car_data["Item"][DynamoDbKeys.PARKING_LOT.value])

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
