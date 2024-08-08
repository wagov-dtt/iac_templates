#!/usr/bin/env python3

from pathlib import Path
import os, subprocess, sys

def run(cmd, shell=False, capture_output=False):
    if capture_output:
        result = subprocess.run(cmd, check=True, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True)
        return result.stdout.strip()
    else:
        subprocess.call(cmd, shell=shell)

def increase_limits():
    sysctl_params = [
        "fs.inotify.max_user_instances=524288",
        "fs.inotify.max_user_watches=524288",
        "fs.file-max=2097152"
    ]
    limits_params = [
        "* soft nofile 1048576",
        "* hard nofile 1048576",
        "root soft nofile 1048576",
        "root hard nofile 1048576"
    ]
    Path("/etc/sysctl.conf").write_text("\n".join(sysctl_params) + "\n", encoding="utf-8")
    Path("/etc/security/limits.conf").write_text("\n".join(limits_params) + "\n", encoding="utf-8")
    run(["sysctl", "-p"])
    run(["sysctl", "--system"])
    os.system("ulimit -n 1048576")

def main(rancher_fqdn):
    if os.geteuid() != 0:
        sys.exit("This script must be run as root (use sudo).")

    increase_limits()
    run("curl -sfL https://get.k3s.io | INSTALL_K3S_CHANNEL=v1.28 INSTALL_K3S_EXEC=\"--kubelet-arg=max-pods=10000\" sh -", shell=True)
    os.environ["KUBECONFIG"] = "/etc/rancher/k3s/k3s.yaml"
    run("curl -fsSL https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash", shell=True)
    run(["helm", "repo", "add", "jetstack", "https://charts.jetstack.io", "--force-update"])
    run(["helm", "install", "cert-manager", "jetstack/cert-manager", "--namespace", "cert-manager", "--create-namespace", "--set", "crds.enabled=true"])
    run(["sleep", "30"])
    run(["helm", "repo", "add", "rancher-stable", "https://releases.rancher.com/server-charts/stable"])
    password = os.urandom(8).hex()
    run(["helm", "install", "rancher", "rancher-stable/rancher", "--namespace", "cattle-system", "--create-namespace",
         "--set", f"hostname={rancher_fqdn}", "--set", f"bootstrapPassword={password}", "--set", "ingress.tls.source=letsEncrypt",
         "--set", f"letsEncrypt.email=admin@{rancher_fqdn}", "--set", "letsEncrypt.ingress.class=traefik"])
    run(["sleep", "30"])
    print(f"Rancher installed at: https://{rancher_fqdn}/dashboard/?setup={password}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("Usage: sudo python3 script.py <rancher_fqdn>")
    main(sys.argv[1])