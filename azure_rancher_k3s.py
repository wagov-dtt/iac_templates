#!/usr/bin/env python3
"""
Rancher K3s Azure Deployment Script

To run in Azure Cloud Shell:
curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/azure_rancher_k3s.py | python3 - <RG NAME/VM PREFIX>
"""

import os, subprocess, random, string, sys, time

if len(sys.argv) != 2:
    sys.exit("Usage: python rancher_k3s.py <name>")

name = sys.argv[1]
location = os.environ.get('AZURE_LOCATION', 'australiaeast')
vm_size = os.environ.get('AZURE_VM_SIZE', 'Standard_E4as_v4')
vm_image = os.environ.get('AZURE_VM_IMAGE', 'Debian:debian-12:12-gen2:latest')
os_disk_size = os.environ.get('AZURE_OS_DISK_SIZE', '512')
dns_name = f"{name}-rancher-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"
fqdn = f"{dns_name}.{location}.cloudapp.azure.com"

commands = [
    f"az group create -n {name} -l {location}",
    f"az vm create -g {name} -n {name}-rancher --image {vm_image} --generate-ssh-keys --size {vm_size} --public-ip-sku Standard --public-ip-address-dns-name {dns_name} --os-disk-size-gb {os_disk_size}",
    f"az network nsg rule create -g {name} --nsg-name {name}-rancherNSG -n AllowHTTP --priority 1010 --destination-port-ranges 80 --access Allow --protocol Tcp",
    f"az network nsg rule create -g {name} --nsg-name {name}-rancherNSG -n AllowHTTPS --priority 1020 --destination-port-ranges 443 --access Allow --protocol Tcp",
]

for cmd in commands:
    subprocess.run(cmd, shell=True, check=True)

print(f"VM created with {os_disk_size}GB OS disk and ports 80, 443 open. Rancher installing at https://{fqdn} ...")

bootstrap = f'curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/rancher_k3s.sh | bash -s {fqdn}'
cmd = f"az vm run-command invoke -g {name} -n {name}-rancher --command-id RunShellScript --scripts '{bootstrap}' --query 'value[0].message' -o tsv"
print(cmd)

# Check if VM is ready for invoke
max_attempts = 10  # 5 minutes (10 * 30 seconds)
attempt = 0
while attempt < max_attempts:
    try:
        check_cmd = f"az vm run-command invoke -g {name} -n {name}-rancher --command-id RunShellScript --scripts 'echo \"VM is ready\"' --query 'value[0].message' -o tsv"
        result = subprocess.run(check_cmd, shell=True, check=True, capture_output=True, text=True)
        if "VM is ready" in result.stdout:
            print("VM is ready for bootstrap")
            break
    except subprocess.CalledProcessError:
        print(f"VM not ready yet. Attempt {attempt + 1}/{max_attempts}")
        time.sleep(30)
    attempt += 1

if attempt == max_attempts:
    print("VM did not become ready in time. Exiting.")
    sys.exit(1)

# Run the bootstrap command
subprocess.run(cmd, shell=True, check=True)