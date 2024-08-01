  #!/bin/bash
  # First arg should be FQDN for rancher
  # K3S pinned to stable version supported by rancher, see https://www.suse.com/suse-rancher/support-matrix/all-supported-versions/
  curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 sh -
  export KUBECONFIG=/etc/rancher/k3s/k3s.yaml
  kubectl create namespace cattle-system
  curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
  helm repo add rancher-stable https://releases.rancher.com/server-charts/stable
  kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
  kubectl wait --for=condition=ready pod -l app.kubernetes.io/instance=cert-manager -n cert-manager --timeout=120s
  helm install rancher rancher-stable/rancher --namespace cattle-system --set hostname=$1
  sleep 10
  echo https://$1/dashboard/?setup=$(kubectl get secret --namespace cattle-system bootstrap-secret -o go-template='{{.data.bootstrapPassword|base64decode}}')