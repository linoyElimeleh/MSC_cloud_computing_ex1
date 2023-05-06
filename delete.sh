KEY_NAME="CC-HW1-EC2-KEY"
KEY_PAIR_FILE=$KEY_NAME".pem"
SEC_GRP="CC_HW1_SEC_GRP"

echo "Terminating all instances"
aws ec2 terminate-instances --instance-ids \
    $(aws ec2 describe-instances --filters  "Name=instance-state-name,Values=pending,running,stopped,stopping" \
    --query "Reservations[].Instances[].[InstanceId]" --output text | tr '\n' ' ') | tr -d '"'

# TODO delete security groups rules before - https://bobbyhadz.com/blog/aws-cli-remove-security-group-rule (there is some dependency)
echo "Deleting security group: $SEC_GRP"
aws ec2 delete-security-group --group-name $SEC_GRP

echo "Deleting key pair: $KEY_NAME"
aws ec2 delete-key-pair --key-name $KEY_NAME
yes | rm -r $KEY_PAIR_FILE
An error occurred (DependencyViolation) when calling the DeleteSecurityGroup operation: resource sg-0706f6451bba82a25 has a dependent object

aws dynamodb delete-table --table-name "ParkingLotDB" | tr -d '"'