from enum import Enum

from flask import Flask, request, jsonify
import boto3
from datetime import datetime

app = Flask(__name__)

TABLE_NAME = 'ParkingLotDB'
dynamodb_client = boto3.resource('dynamodb')
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

    ticket_id = calculate_unique_ticket_id(entry_time, plate_number)

    parking_lot_table.put_item(Item={DynamoDbKeys.TICKET_ID.value: ticket_id,
                                     DynamoDbKeys.ENTRY_TIMESTAMP.value: entry_time.strftime('%s'),
                                     DynamoDbKeys.PLATE_NUMBER.value: plate_number,
                                     DynamoDbKeys.PARKING_LOT.value: parking_lot})

    return jsonify({'ticketId': ticket_id})


def calculate_unique_ticket_id(datetime, plate_number):
    return str(plate_number) + '.' + datetime.strftime('%s')


@app.route('/exit', methods=['POST'])
def exit_parking():
    ticket_id = request.args.get('ticketId')

    car_data = parking_lot_table.get_item(Key={DynamoDbKeys.TICKET_ID.value: ticket_id})
    if car_data is None:
        return jsonify({'error': 'Invalid ticketId'})
    entry_time = datetime.fromtimestamp(int(car_data["Item"][DynamoDbKeys.ENTRY_TIMESTAMP.value]))
    plate_number = car_data["Item"][DynamoDbKeys.PLATE_NUMBER.value]
    parking_lot = car_data["Item"][DynamoDbKeys.PARKING_LOT.value]

    # calculate parked time in minutes
    parked_time_minutes = int((datetime.now() - entry_time).total_seconds() / 60)

    # calculate charge based on parked time (rounded up to nearest 15 minutes)
    charge = round(parked_time_minutes / 15) * 2.5

    return jsonify({'licensePlate': plate_number,
                    'parkedTime': parked_time_minutes,
                    'parkingLot': parking_lot,
                    'charge': charge})


if __name__ == '__main__':
    app.run()
