# Infrastructure as Code templates

Some convenient quick starts for use in public cloud environments. Goal is to get a CNCF compliant k8s environment established with minimal complexity and ability to scale for production requirements.


## AWS quickstart

### Launch a rancher cluster + manager

Deploy a generated [cloud template](https://wagov-dtt.github.io/iac_templates/rancher_setup/rancher_quickstart.html) using [cloudformation](https://ap-southeast-2.console.aws.amazon.com/cloudformation/home?region=ap-southeast-2#/stacks/create) (Upload a template file). It should output a URL that you can visit to configure rancher, note on first run you can also setup a CNAME or equivalent dns alias, and reconfigure the primary control plane endpoint (it will use letsencrypt ACME http-challenge to automatically sort out SSL).

## Azure quickstart

[Open Azure Cloud Shell](https://shell.azure.com/bash)

Below content slightly dated, todo: move to simple templates + rancher guidance.

## Kuberenetes Platform as a Service

Rough guidance on how to get a production ready kubernetes environment in azure, managed by rancher, with fleet for gitops working.

Below will setup a resource group `$NAME` and a rancher vm `$NAME-rancher` accessible from the internet. See the [`rancher_k3s.sh`](rancher_k3s.sh) for the script which should run on any linux server that supports [k3s](https://docs.k3s.io/installation/requirements#operating-systems).

```bash
export NAME=<mycoolname>
curl -sL https://raw.githubusercontent.com/adonm/iac_templates/main/azure_rancher_k3s.py | python3 - $NAME
```

## AKS Automatic cluster provisioning

You can have several (i.e. 100s) of clusters managed by the one rancher instance above. Makes sense to separate by development team and information sensitivity where possible.

Follow the [AKS Automatic install guide](https://learn.microsoft.com/en-us/azure/aks/learn/quick-kubernetes-automatic-deploy?pivots=azure-cli). Wait for about 15 minutes for the cluster to fully initialise, then follow the rancher guide to [register an existing cluster](https://ranchermanager.docs.rancher.com/how-to-guides/new-user-guides/kubernetes-clusters-in-rancher-setup/register-existing-clusters) (generic, to avoid needing cloud credential setup), and use the kubectl register command below:

```bash
az aks create --resource-group $NAME --name $NAME-01 --sku automatic
# Wait 15 mins
az aks command invoke --resource-group $NAME --name $NAME-01 --command "<kubectl-register-cmd-from-rancher>"
```

### GitOps & ingress/storage etc

Below is manual setup, that should be configured in fleet as a template repo to do automatically for aks automatic clusters

Once manager setup with auth etc, then use the kubectl cmd line in rancher to run the below (TODO move to gitops / [fleet](https://fleet.rancher.io)):

```bash
# Ingress and letsencrypt setup
helm repo add jetstack https://charts.jetstack.io
helm repo update
helm install cert-manager jetstack/cert-manager --set crds.enabled=true -n cert-manager --create-namespace
```

Import the below to ensure core rancher agent doesn't get evicted (see [Karpenter Disruption Budgets](https://karpenter.sh/docs/concepts/disruption/#disruption-budgets))

```yaml
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: cattle-cluster-agent-pdb
  namespace: cattle-system
spec:
  selector:
    matchLabels:
      app: cattle-cluster-agent
  minAvailable: 1
```

Import the below yaml and validate ssl works with a whoami container:

```yaml
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    email: your-email@example.com
    server: https://acme-v02.api.letsencrypt.org/directory
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          ingressClassName: webapprouting.kubernetes.azure.com
```

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: your-app-ingress
  namespace: your-app-namespace  # Replace with your app's namespace
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - your-app.YOUR-LB-IP.sslip.io
    secretName: your-app-tls
  rules:
  - host: your-app.YOUR-LB-IP.sslip.io
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: your-service
            port: 
              number: 80
```
