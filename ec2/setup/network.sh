# Mostly extracted from https://github.com/doctorray117/minecraft-ondemand/blob/main/minecraft-ecsfargate-watchdog/watchdog.sh

INSTANCE_ID=
HOSTED_ZONE_ID=

PUBLICIP=$(aws ec2 describe-instances --instance-ids $INSTANCE_ID  --query 'Reservations[*].Instances[*].PublicIpAddress' --output text)
cat << EOF > minecraft-dns.json
{
  "Comment": "Public IP change for Minecraft Server",
  "Changes": [
    {
      "Action": "UPSERT",
      "ResourceRecordSet": {
        "Name": "<subdomain>.<yourdomain>",
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