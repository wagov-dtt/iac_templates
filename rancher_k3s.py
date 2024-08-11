#!/usr/bin/env python3
import os, sys
from pathlib import Path
from subprocess import call

def increase_limits():
    sysctl_params = """
fs.inotify.max_user_instances = 8192
fs.inotify.max_user_watches = 524288
vm.max_map_count = 262144
"""
    Path("/etc/sysctl.d/99-k3s-densepod.conf").write_text(sysctl_params.strip())
    call(["sysctl", "--system"])

def main(rancher_fqdn, password):
    increase_limits()
    call('curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 INSTALL_K3S_EXEC="--kubelet-arg=max-pods=900" sh -', shell=True)
    os.environ["KUBECONFIG"] = "/etc/rancher/k3s/k3s.yaml"
    call("curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash", shell=True)
    call(["helm", "repo", "add", "jetstack", "https://charts.jetstack.io", "--force-update"])
    call(["helm", "install", "cert-manager", "jetstack/cert-manager", "--namespace", "cert-manager", "--create-namespace", "--set", "crds.enabled=true"])
    call(["sleep", "30"])
    call(["helm", "repo", "add", "rancher-stable", "https://releases.rancher.com/server-charts/stable"])
    call(["helm", "install", "rancher", "rancher-stable/rancher", "--namespace", "cattle-system", "--create-namespace",
         "--set", f"hostname={rancher_fqdn}", "--set", f"bootstrapPassword={password}", "--set", "ingress.tls.source=letsEncrypt",
         "--set", f"letsEncrypt.email=admin@{rancher_fqdn}", "--set", "letsEncrypt.ingress.class=traefik"])
    call(["sleep", "30"])
    print(f"Rancher installed at: https://{rancher_fqdn}/dashboard/?setup={password}")

if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: sudo python3 script.py <rancher_fqdn> <password>")
    main(sys.argv[1], sys.argv[2])