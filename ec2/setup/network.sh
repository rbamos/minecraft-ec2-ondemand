INSTANCE_ID=i-0db1ce3d8171c7e44
HOSTED_ZONE_ID=Z0061764DPB0OHYDP9A4
HOSTNAME=dw20.mcserver.cyou

setup_zone() {
    PUBLICIP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID  --query 'Reservations[*].Instances[*].PublicIpAddress' --output text)

    aws route53 list-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID | grep "$PUBLICIP" &> /dev/null
    
    if [ $? == 0 ]; then
	return 0
    fi
    
    cat << EOF > minecraft-dns.json
{
  "Comment": "Minecraft IP change",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "$HOSTNAME",
        "Type": "A",
        "TTL": 30,
        "ResourceRecords": [
          {
            "Value": "$PUBLICIP"
          }
        ]
      }
    }
  ]
}
EOF

    aws route53 change-resource-record-sets --hosted-zone-id $HOSTED_ZONE_ID --change-batch file://minecraft-dns.json

    echo "Updated $HOSTNAME to $PUBLICIP"
}

while : ; do
      setup_zone
      sleep 10s
done
      
