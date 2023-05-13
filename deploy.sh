KEY_NAME="CC-HW1-EC2-KEY"
KEY_PAIR_FILE=$KEY_NAME".pem"
SEC_GRP="CC_HW1_SEC_GRP"
MY_IP=$(curl --silent ipinfo.io/ip)

echo "PC_IP_ADDRESS: $MY_IP"

echo "creating ec2 key pair: $KEY_NAME"
aws ec2 create-key-pair \
    --key-name $KEY_NAME \
    --key-type rsa \
    --key-format pem \
    --query "KeyMaterial" \
    --output text > $KEY_PAIR_FILE
chmod 400 $KEY_PAIR_FILE

echo "create security group $SEC_GRP"
aws ec2 create-security-group --group-name $SEC_GRP --description "HW1 security group" | tr -d '"'

echo "allow ssh from $MY_IP only"
aws ec2 authorize-security-group-ingress        \
    --group-name $SEC_GRP --port 22 --protocol tcp \
    --cidr $MY_IP/32 | tr -d '"'

aws ec2 authorize-security-group-ingress        \
    --group-name $SEC_GRP --port 5000 --protocol tcp \
    --cidr $MY_IP/32 | tr -d '"'

echo "Create table"
aws dynamodb create-table \
    --table-name "ParkingLotDB" \
    --attribute-definitions AttributeName=ticket_id,AttributeType=S \
    --key-schema AttributeName=ticket_id,KeyType=HASH \
    --provisioned-throughput ReadCapacityUnits=1,WriteCapacityUnits=1 | tr -d '"'

aws dynamodb describe-table --table-name ParkingLotDB | grep TableStatus

echo "Creating role"
aws iam create-role --role-name dynamodb-full-access-role --assume-role-policy-document file://EC2_Trust_Policy.json | tr -d '"'
aws iam attach-role-policy --role-name dynamodb-full-access-role --policy-arn arn:aws:iam::aws:policy/AmazonDynamoDBFullAccess
aws iam create-instance-profile --instance-profile-name dynamodb-full-access-role-instance-profile
aws iam add-role-to-instance-profile --role-name dynamodb-full-access-role --instance-profile-name dynamodb-full-access-role-instance-profile

echo "Launching EC2 instance"
RUN_INSTANCES=$(aws ec2 run-instances   \
    --image-id "ami-04aa66cdfe687d427"  \
    --instance-type t2.micro            \
    --key-name $KEY_NAME                \
    --security-groups $SEC_GRP)

INSTANCE_ID=$(echo $RUN_INSTANCES | jq -r '.Instances[0].InstanceId')

aws ec2 wait instance-running --instance-ids $INSTANCE_ID

echo "Associate iam instance profile"
aws ec2 associate-iam-instance-profile --instance-id $INSTANCE_ID --iam-instance-profile Name=dynamodb-full-access-role-instance-profile | tr -d '"'

PUBLIC_IP=$(aws ec2 describe-instances  --instance-ids $INSTANCE_ID | \
            jq -r '.Reservations[0].Instances[0].PublicIpAddress')

echo "EC2 instance is up at: $PUBLIC_IP"

echo "Uploading files to instance"
scp -i $KEY_PAIR_FILE -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=60" app/app.py ubuntu@$PUBLIC_IP:/home/ubuntu/
scp -i $KEY_PAIR_FILE -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=60" requirements.txt ubuntu@$PUBLIC_IP:/home/ubuntu/

echo "Updating and starting app"
ssh -T -o "StrictHostKeyChecking=no" -o "ConnectionAttempts=10" -i $KEY_PAIR_FILE ubuntu@$PUBLIC_IP << EOF
    sudo apt-get update -y
    sudo apt-get upgrade -y
    sudo apt update -y
    sudo apt upgrade -y
    sudo apt install python3-pip -y
    sudo pip3 install --upgrade pip
    pip3 install -r requirements.txt
    export FLASK_APP=app/app.py
    nohup python3 -m flask run --host=0.0.0.0 &>/dev/null &
    exit
EOF