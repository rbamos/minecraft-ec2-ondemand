# Run Minecraft on EC2 for a reasonable fee
This repository contains instructions and scripts for running a minecraft server on EC2 on-demand.

Feel free to file an issue or reach out directly with any questions.

## Motivation
Running a modded Minecraft server on a dedicated host can cost $35+ per month for a server with adequate performance.
That's nearly the lifetime price of Minecraft, or a few months' subscription for other games. This makes running a cloud
modded Minecraft server pretty cost-prohibitive.

Amazon AWS lets you pay for the resources you use, and most people aren't playing Minecraft 24/7, so this provides a
work-around -- we can turn off our server when it's not in use and cut that cost down something manageable. I'm
estimating around $10/month for a modded server.

The challenge is in enabling and disabling the server as-needed. The core solution comes from
[doctorray117](https://github.com/doctorray117/minecraft-ondemand), who showed how to launch a Minecraft server when
a DNS request is made to that server.

## Credit

These instructions lean heavily on 
[doctorray117's Minecraft-OnDemand project](https://github.com/doctorray117/minecraft-ondemand), which does this but
with Docker. Many thanks to them.

If you're looking for something simpler to set up, that project has an Infrastructure as Code implementation for faster
deployment.

I wanted to tweak that to run on EC2 for better performance, faster boot, and easier server console access.

## Prerequesites
1. You need an AWS account.
2. You need a domain name with the domain or a subdomain on Route53 (Amazon's DNS service).
3. You should have a decent understanding of Bash and how to set up a Minecraft server .
4. An understanding of AWS. This guide doesn't go into all the details for now (if you want more details, please
file an issue so I know there's demand for it).

## Billing alert
I've heard tons of horror stories about people getting surprise bills with AWS. Don't get caught floating a $500 bill
because you forgot to turn off an instance you didn't mean to launch.

A Budget can be set up to alert you when this happens. I *strongly* recommend setting one. This is done under Billing ->
 Budget.

The cost of this project will be (roughly):
* $0.50/month for Route53
* $0.17c/hour usage for EC2 (if using `c5.xlarge`)
* $1.50/month for EBS (if using 30GB)
* $0.009/hr/user in network egress fees (very rough estimate) 
* A few pennies for Lambda
* $2/year for your domain name, if you go with a low cost TLD

Please let me know what you are charged so I give a more accurate representation of cost.

For your first year of AWS, you get up to 30GB of EBS free as part of AWS Free Tier.

### Actual bills
During two months of heavy usage, I had bills of $18.78 and $18.19. During a moderate usage month, I had a bill of 
$11.28. During an idle month I had a bill of $1.30.

## Decide if you are using the shut down or hibernate strategy
There are two strategies for disabling your Minecraft instance.

**Shut down**: This shuts down the instance. It's quick to shut down, but it's slow to boot. This requires less EBS
volume space, and so is cheaper by about $0.50/mo.

**Hibernate**: This hibernates the instance. Hibernation is slow, but booting is rapid. This will add around $0.50/mo
to your cost. Even though going into hibernation is slow, AWS does not charge for your instance while it is shutting
down.

## Launch an EC2 instance
You should set up an EC2 instance. What resources you'll need depends on if you are running modpacks, how many users you
have, etc.

I recommend looking at the c-series (compute optimized) instances. This will be your biggest expense so choose
carefully. [Price comparison](https://aws.amazon.com/ec2/pricing/on-demand/). I went with `c5.xlarge`.

Set up an SSH key.

Your EC2 instance will need to be assigned to a role with the following permissions:
* Route53: ChangeResourceRecordSets on your domain's hosted zone
* EC2: DescribeInstances on your instance
* EC2: StopInstances on your instance, if you are using the hibernate strategy

Make sure your security group allows ingress on ports 22 (SSH) and 25565 (Minecraft)

Set the EBS volume to encrypted. Consider the size of your EBS volume carefully. I found 30GB to be stable for me. 20GB
may be adequate. Note: 30GB is included in free tier.

If using the hibernate strategy, enable hibernation. You will need to allocate additional space to the EBS volume for 
your RAM e.g. if you enable hibernation on an instance with 8GB of ram, you'll need to add an additional 8GB of space to
 EBS. **You cannot enable hibernation later without recreating the instance.**

## Set up Minecraft
SSH into your EC2 instance. Install the Minecraft server.

There are lots of ways to set up Minecraft. I went with an FTB server but the choice is yours. Ultimately, you should
have your server installed in
```bash
~/minecraft/
```
If your installation doesn't include it, create a file
```bash
~/minecraft/start.sh
```
which starts your server. Make sure to give it enough RAM but don't do too much. For my `c5.xlarge`, I found `-Xmx5G` to
be the right size.

## Set up the start-up routine
Install crontab and other prerequesites. On Amazon Linux 2023, this is done with 

```bash
yum install cronie python3-pip java
pip3 install --upgrade --user awscli mcstatus libtmux
```

There may be more dependencies; install them if requested.

From the `ec2/` folder, copy the contents of the `setup/` folder into `~`. Go through each of the files; there are
fields for you to fill out. Specifically:

* `monitor.py`: If not using the hibernate strategy, you do not need to modify this file
  * `HIBERNATE`: `True`/`False` if you want to use the shut down or hibernate strategy
  * `INSTANCE_ID`: Your EC2 instance ID (only required for hibernating)
* `network.sh`:
  * `INSTANCE_ID`: Your EC2 instance ID
  * `HOSTED_ZONE_ID`: Your Route53 hosted zone ID
  * `HOSTNAME`: Your hostname (e.g. minecraft.example.com)

Set up the cron job:
```bash
crontab -e
```
And add:
```
@reboot ~/setup/start.sh
* * * * * ~/setup/start.sh
```

### Test everything
First test the network setup works:
```bash
cd ~/setup
./network.sh
```

From your local machine, ping the Minecraft server
```bash
ping minecraft.example.com
```
and make sure it's live.

Next, test that starting Minecraft works
```bash
cd ~/minecraft
./start.sh
```
Make sure the Minecraft server starts and is reachable. Then stop the server.

Lastly, test everything together. Reboot the instance. You should have 2 tmux sessions running:
```bash
tmux list-sessions
```
The first will be `minecraft`, the second `monitor`. You can connect to the sessions with
```bash
tmux at -t <session_name>
```
You can exit the session without killing the process with `ctrl+b` then `d`.

Make sure both sessions are running. Let the monitor time out (Default: 30 minutes) to verify it shuts down correctly.

## Set up an SNS topic
Create an SNS topic. Subscribe your email to it.

## Set up your Lambdas
Check `lambda/` for the code.

You will need two lambdas.

### Launcher
The code for this lambda is in `launcher.py`.

Create a role for this Lambda; it needs the following permissions:
* EC2: DescribeInstances on your instance
* EC2: StartInstance on your instance

Hit deploy & test it. Your EC2 instance should start if it's not already running.

### Duration monitor
The code for this lambda is in `duration_monitor.py`. This lambda is an "in case of emergency" monitor that alerts you
if the server has been running for 8 or more hours.

Create a role for this Lambda; it needs the following permissions:
* EC2: DescribeInstances on your instance
* SNS: Publish on your SNS topic

Under Congiruation->Trigger, add an EventBridge trigger with the following expression `rate(2 hours)`

To test it, drop `MAX_TIME` to 0 hours. You should receive an email. The change `MAX_TIME` back to 8 hours.

## Set up CloudWatch
This is the magic of doctorray117's original project. I suggest following
[the original instructions](https://github.com/doctorray117/minecraft-ondemand#cloudwatch).

## Connecting to your game
You should be done now! Boot up Minecraft, add your server to your server list. When the DNS request is made, the EC2
instance will start to boot. Wait a few minutes and your game will be live.

Remmeber that the first time the world launches is always the slowest.

### Pre-booting your servers
Your players may wish for a quicker boot sequence. They can preboot the server by attempting to visit your server's
domain name in their browser. This will trigger the lambda and start the boot process. With local Minecraft taking a few
minutes to load anyways, this means the wait should be minimal.

Another option is to embed a 1x1 `<img>` that points to your server's domain in a website you host; you can point your 
players to that site. Be cautious with this, as a webcrawl may also boot your server.

## Possible improvements
* ~~Better boot time could be achieved by hibernating instead of shutting down the EC2 instance~~
* Moving activity monitoring & shutdown to another instance could provide better robustness
