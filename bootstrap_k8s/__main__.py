#!/usr/bin/env python3
# To build bootstrap_k8s.pyz: python -m zipapp -c bootstrap_k8s
import os, zipfile, tempfile
from pathlib import Path
from subprocess import run

rancher_fqdn = os.environ.get("RANCHER_FQDN", False)

def read_text(file_name):
    with zipfile.ZipFile(Path(__file__).parent) as zf:
        with zf.open(f"config/{file_name}") as f:
            return f.read().decode("utf-8")

def azure_k8s_setup():
    run("""
kubectl apply -f nodes.yaml
helm repo add traefik https://traefik.github.io/charts
helm repo add jetstack https://charts.jetstack.io
helm repo add longhorn https://charts.longhorn.io
helm repo add rancher-latest https://releases.rancher.com/server-charts/latest
helm repo update
helm install --atomic traefik traefik/traefik -n kube-system -f traefik-values.yaml
helm install --atomic cert-manager jetstack/cert-manager --namespace cert-manager --create-namespace --set crds.enabled=true
helm install --atomic longhorn longhorn/longhorn --namespace longhorn-system --create-namespace  --set defaultSettings.defaultDataLocality=best-effort \
--set defaultSettings.storageReservedPercentageForDefaultDisk=0 --set defaultSettings.createDefaultDiskLabeledNodes=True
        """, shell=True)
    if rancher_fqdn:
        run("helm install --atomic rancher rancher-latest/rancher --create-namespace --namespace cattle-system"
            f" --set ingress.tls.source=letsEncrypt --set letsEncrypt.ingress.class=traefik --set hostname={rancher_fqdn}"
            f" --set letsEncrypt.email={rancher_fqdn}@maildrop.cc", shell=True)

def main():
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        Path("nodes.yaml").write_text(read_text("nodes.yaml"))
        Path("traefik-values.yaml").write_text(read_text("traefik-values.yaml"))
        azure_k8s_setup()

if __name__ == "__main__":
    main()