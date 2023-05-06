from enum import Enum

from flask import Flask, request, jsonify
import boto3
import datetime

app = Flask(__name__)

# dictionary to store parking lot data, key = ticket id, value = [license plate, parking lot id, entry time]
parking_lot_data = {}

TABLE_NAME = 'ParkingLotDB'
dynamodb_client = boto3.client('dynamodb')


class DynamoDbKeys(Enum):
    TICKET_ID = 'ticket_id'
    ENTRY_TIMESTAMP = 'entry_timestamp'
    PLATE_NUMBER = 'plate_number'
    PARKING_LOT = 'parking_lot'


@app.route('/entry', methods=['POST'])
def entry_parking():
    # POST /entry?plate=123-123-123&amp;parkingLot=382
    entry_time = datetime.datetime.now()
    plate_number = request.args.get('plateNumber')
    parking_lot = request.args.get('parkingLot')

    # generate ticket id by concatenating plate and current timestamp
    ticket_id = calculate_unique_ticket_id(entry_time, plate_number)

    dynamodb_client.put_item(TableName=TABLE_NAME,
                             Item={DynamoDbKeys.TICKET_ID.value: {'S': ticket_id},
                                   DynamoDbKeys.ENTRY_TIMESTAMP.value: {'S': entry_time.strftime('%s')},
                                   DynamoDbKeys.PLATE_NUMBER.value: {'S': plate_number},
                                   DynamoDbKeys.PARKING_LOT.value: {'S': parking_lot}})

    return jsonify({'ticketId': ticket_id})


def calculate_unique_ticket_id(datetiem, plate_number):
    return str(plate_number) + '.' + datetiem.strftime('%s')


@app.route('/exit', methods=['POST'])
def exit_parking():
    # POST /exit?ticketId=1234
    ticket_id = request.args.get('ticketId')

    # retrieve entry data from dictionary
    entry_data = parking_lot_data.get(ticket_id)

    car_data = dynamodb_client.get_item(TableName=TABLE_NAME,
                                        Key={DynamoDbKeys.TICKET_ID.value: {'S': ticket_id}})
    if car_data is None:
        return jsonify({'error': 'Invalid ticketId'})
    entry_time = datetime.datetime.fromtimestamp(int(car_data["Item"][DynamoDbKeys.ENTRY_TIMESTAMP.value]['S']))
    plate_number = car_data["Item"][DynamoDbKeys.PLATE_NUMBER.value]['S']
    parking_lot = car_data["Item"][DynamoDbKeys.PARKING_LOT.value]['S']

    # calculate parked time in minutes
    parked_time = int((datetime.datetime.now() - entry_time).total_seconds() / 60)

    # calculate charge based on parked time (rounded up to nearest 15 minutes)
    charge = round(parked_time / 15) * 10

    return jsonify(
        {'licensePlate': plate_number, 'parkedTime': parked_time, 'parkingLot': parking_lot, 'charge': charge})


if __name__ == '__main__':
    app.run()
