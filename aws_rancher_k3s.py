#!/usr/bin/env python3
"""
Rancher K3s AWS Deployment Script (untested)

To run in AWS CloudShell:
curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/aws_rancher_k3s.py | python3 - <INSTANCE NAME PREFIX>
"""

import os, subprocess, random, string, sys, json, time

if len(sys.argv) != 2:
    sys.exit("Usage: python aws_rancher_k3s.py <name>")

name = sys.argv[1]
region = os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')  # Sydney
instance_type = os.environ.get('AWS_INSTANCE_TYPE', 'r6a.2xlarge')  # 32GB RAM, high memory series
ami_id = os.environ.get('AWS_AMI_ID', 'ami-0310483fb2b488153')  # Debian 12 in ap-southeast-2, change as needed
volume_size = os.environ.get('AWS_VOLUME_SIZE', '512')
dns_name = f"{name}-rancher-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"

# Create a security group
sg_create_output = subprocess.check_output(f"aws ec2 create-security-group --group-name {name}-sg --description 'Security group for Rancher K3s'", shell=True)
sg_id = json.loads(sg_create_output)['GroupId']

# Add inbound rules to the security group
subprocess.run(f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port 22 --cidr 0.0.0.0/0", shell=True, check=True)
subprocess.run(f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port 80 --cidr 0.0.0.0/0", shell=True, check=True)
subprocess.run(f"aws ec2 authorize-security-group-ingress --group-id {sg_id} --protocol tcp --port 443 --cidr 0.0.0.0/0", shell=True, check=True)

# Create EC2 instance
instance_output = subprocess.check_output(f"""
aws ec2 run-instances 
    --image-id {ami_id} 
    --instance-type {instance_type} 
    --security-group-ids {sg_id} 
    --block-device-mappings '[{{"DeviceName":"/dev/xvda","Ebs":{{"VolumeSize":{volume_size},"VolumeType":"gp3"}}}}]'
    --tag-specifications 'ResourceType=instance,Tags=[{{Key=Name,Value={name}-rancher}}]'
    --iam-instance-profile Name=AmazonSSMRoleForInstancesQuickSetup
""", shell=True)

instance_id = json.loads(instance_output)['Instances'][0]['InstanceId']

print(f"Instance {instance_id} created with {volume_size}GB root volume and ports 22, 80, 443 open.")

# Wait for the instance to be running
subprocess.run(f"aws ec2 wait instance-running --instance-ids {instance_id}", shell=True, check=True)

# Get the public DNS name of the instance
dns_output = subprocess.check_output(f"aws ec2 describe-instances --instance-ids {instance_id} --query 'Reservations[0].Instances[0].PublicDnsName' --output text", shell=True)
public_dns = dns_output.decode().strip()

print(f"Instance is now running. Public DNS: {public_dns}")
print("Waiting for instance to be ready for SSM...")

# Wait a bit for SSM to be ready
time.sleep(60)

print("Rancher K3s is being installed...")

# Install Rancher K3s using AWS Systems Manager Send-Command
bootstrap = f'curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/rancher_k3s.sh | bash -s {public_dns}'
cmd_output = subprocess.check_output(f"""
aws ssm send-command 
    --instance-ids {instance_id} 
    --document-name "AWS-RunShellScript" 
    --parameters 'commands=["{bootstrap}"]' 
    --output text 
    --query "Command.CommandId"
""", shell=True)

cmd_id = cmd_output.decode().strip()

# Wait for the command to complete
subprocess.run(f"aws ssm wait command-executed --command-id {cmd_id} --instance-id {instance_id}", shell=True, check=True)

print(f"Rancher K3s installation complete. You can access it at https://{public_dns}")