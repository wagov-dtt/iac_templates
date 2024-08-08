# Notes on setting up rancher in AWS
Eventually script maybe to use in AWS cloud shell?

## Create a VPC

Public subnet only, 3 availability zones, internet gateway and route table. Likely will need a load balancer configured pointing to a group of rancher vms.

## Create a Suse EC2 instance

SUSE Linux Enterprise Server 15 SP6 (HVM, 64-bit, SSD-Backed)
r6a.xlarge
1 volume(s) - 512 GiB (encrypted)

## Run through rke2 and rancher setup on instance

all of below can be one shell script, todo. Using rke2 instead of k3s as want to try and keep storage/network plane consistent (cilium/longhorn) which is easier with rke2.

https://docs.rke2.io/install/quickstart

https://docs.rke2.io/cluster_access

https://ranchermanager.docs.rancher.com/getting-started/installation-and-upgrade/install-upgrade-on-a-kubernetes-cluster
