#!/usr/bin/env python3
import sys, subprocess, time, json

def run(cmd):
    return subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)

def setup_aks_preview():
    # Set up AKS preview extension and register feature flags
    run("az extension add --name aks-preview")
    run("az extension update --name aks-preview")

    features = [
        "EnableAPIServerVnetIntegrationPreview", "NRGLockdownPreview", "SafeguardsPreview",
        "NodeAutoProvisioningPreview", "DisableSSHPreview", "AutomaticSKUPreview"
    ]
    for feature in features:
        run(f"az feature register --namespace Microsoft.ContainerService --name {feature}")

    print("Waiting for feature flags to register...")
    while True:
        status = json.loads(run("az feature show --namespace Microsoft.ContainerService --name AutomaticSKUPreview").stdout)['properties']['state']
        if status == 'Registered':
            print("AutomaticSKUPreview is now registered.")
            break
        print(f"Current status: {status}. Checking again in 10 seconds...")
        time.sleep(10)

    run("az provider register --namespace Microsoft.ContainerService")

def setup_cluster(name):
    # Create resource group and AKS cluster
    run(f"az group create --name {name} --location eastus")
    run(f"az aks create --resource-group {name} --name {name} --sku automatic")
    run(f"az aks enable-addons --addons azure-defender,azure-policy,backup --resource-group {name} --name {name}")

def setup_rancher_and_aso2(name):
    # Set up Rancher and ASO2
    run(f"az aks get-credentials --resource-group {name} --name {name} --overwrite-existing")
    for repo in ["rancher-latest https://releases.rancher.com/server-charts/latest", 
                 "aso2 https://raw.githubusercontent.com/Azure/azure-service-operator/main/v2/charts"]:
        run(f"helm repo add {repo}")
    run("helm repo update")
    run("kubectl apply -f https://github.com/jetstack/cert-manager/releases/download/v1.5.1/cert-manager.yaml")
    run("helm install rancher rancher-latest/rancher --namespace cattle-system --create-namespace --set hostname=rancher.my-domain.com --set bootstrapPassword=admin")
    run("helm install aso2 aso2/azure-service-operator --namespace azure-service-operator-system --create-namespace")

def main(name):
    setup_aks_preview()
    setup_cluster(name)
    setup_rancher_and_aso2(name)
    print("Deployment and setup completed successfully.")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python rancher_aks.py <cluster_name>")
        sys.exit(1)
    main(sys.argv[1])