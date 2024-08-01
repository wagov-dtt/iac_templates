#!/usr/bin/env python3
"""
Rancher K3s Azure Deployment Script

To run in Azure Cloud Shell:
curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/rancher_k3s.py | python3 - <RG NAME/VM PREFIX>
"""

import os, subprocess, random, string, sys, time, tempfile

if len(sys.argv) != 2:
    sys.exit("Usage: python rancher_k3s.py <name>")

name = sys.argv[1]
location = os.environ.get('AZURE_LOCATION', 'australiaeast')
vm_size = os.environ.get('AZURE_VM_SIZE', 'Standard_E4as_v4')
vm_image = os.environ.get('AZURE_VM_IMAGE', 'Debian:debian-12:12-gen2:latest')
dns_name = f"{name}-rancher-{''.join(random.choices(string.ascii_lowercase + string.digits, k=4))}"
fqdn = f"{dns_name}.{location}.cloudapp.azure.com"

cloud_init = f"""#cloud-config
runcmd:
  - curl -sfL https://get.k3s.io | sh -
  - kubectl create namespace cattle-system
  - curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  - helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
  - kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
  - kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s
  - helm install rancher rancher-stable/rancher --namespace cattle-system --set hostname={fqdn}
"""

temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
temp_file.write(cloud_init)

commands = [
    f"az group create -n {name} -l {location}",
    f"az vm create -g {name} -n {name}-rancher --image {vm_image} --generate-ssh-keys --size {vm_size} --public-ip-sku Standard --public-ip-address-dns-name {dns_name} --custom-data {temp_file.name} --assign-identity --role contributor --scope /subscriptions/$(az account show --query id -o tsv)/resourceGroups/{name}",
    f"az backup vault create -n {name}Vault -g {name} -l {location}",
    f"az backup protection enable-for-vm -g {name} --vault-name {name}Vault --vm {name}-rancher --policy-name EnhancedPolicy"
]

for cmd in commands:
    subprocess.run(cmd, shell=True, check=True)

os.remove(temp_file.name)

print(f"VM created with backups. Rancher installing at https://{fqdn}")

kubectl_cmd = r'sudo kubectl get secret --namespace cattle-system bootstrap-secret -o go-template="{{.data.bootstrapPassword|base64decode}}"'
az_cmd = f"az vm run-command invoke -g {name} -n {name}-rancher --command-id RunShellScript --scripts '{kubectl_cmd}'"

for attempt in range(30):
    try:
        result = subprocess.run(az_cmd, shell=True, check=True, capture_output=True, text=True)
        bootstrap_password = result.stdout.strip().split('\n')[-1]
        if bootstrap_password:
            print(f"\nRancher ready at https://{fqdn}")
            print(f"Bootstrap Password: {bootstrap_password}")
            break
    except subprocess.CalledProcessError:
        pass
    time.sleep(20)
    if attempt % 3 == 2:
        print(f"Waiting for Rancher... (Attempt {attempt+1}/30)")
else:
    print("\nTimed out waiting for Rancher. Check VM logs.")

