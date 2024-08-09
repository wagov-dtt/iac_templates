# Notes on setting up rancher in AWS
This is just the first node, which can be used to configure and build a lot more resources with the appropriate credentials delegated to it. Eventually script maybe to use in AWS cloud shell?

## Create a VPC

Public subnet only, 3 availability zones, internet gateway and route table. Likely will need a load balancer configured pointing to a group of rancher vms.

## Create a Suse EC2 instance, make sure it has ssm manager role.

- SUSE Linux Enterprise Server 15 SP6 (HVM, 64-bit, SSD-Backed)
- r6a.xlarge
- 1 volume(s) - 512 GiB (encrypted)
- Auto attach public ip to intfc one
- Set IAM policy to SSM friendly ec2 instance one

## Run through k3s and rancher setup on instance

Connect to the instance with SSM manager, and run the following python script to setup k3s and rancher:

```bash
curl -sL https://raw.githubusercontent.com/wagov-dtt/iac_templates/main/rancher_k3s.py | python3 - {fqdn}
```

Navigate to the url shown, change password and use the cluster manager to create a custom RKE2 clusters, copy the register command for the nodes below (run it on the nodes using SSM connect)

## Nodes - Create a Suse EC2 launch template and autoscaling group, make sure it has ssm manager role.

- SUSE Linux Enterprise Server 15 SP6 (HVM, 64-bit, SSD-Backed)
- i4i.xlarge
- OS volume - 64GB (encrypted)
- Auto attach public ip to intfc one
- Set IAM policy to SSM friendly ec2 instance one

Once cluster up, install longhorn/monitoring/neuvector through 'cluster tools' in rancher ui.