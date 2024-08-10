#!/usr/bin/env python3

import sys, os, subprocess, tempfile

env = os.environ.get
cwd = os.getcwd()
name = sys.argv[1]

eks_cluster = f"""
apiVersion: eksctl.io/v1alpha5
kind: ClusterConfig
metadata:
  name: {name}
  region: {env('AWS_REGION', 'ap-southeast-2')}
cloudWatch:
  clusterLogging:
    enableTypes: ["*"]
addonsConfig:
  disableDefaultAddons: true
addons:
  - name: coredns
  - name: amazon-cloudwatch-observability
  - name: aws-guardduty-agent
iam:
  withOIDC: true
managedNodeGroups:
- name: workers
  instanceType: {env('AWS_INSTANCE_TYPE' ,'r6a.xlarge')}
  minSize: 3
  maxSize: 6
  desiredCapacity: 3
  privateNetworking: true
  volumeSize: {env('AWS_VOLUME_SIZE', 512)}
  maxPodsPerNode: 1000
  amiFamily: AmazonLinux2023
  spot: true
"""

def run(cmd: str) -> str:
    print(cmd)
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        print(eks_cluster)
        open("eks-config.yaml", "w").write(eks_cluster.split("managedNodeGroups:")[0])
        run("curl -sL https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz | tar xz")
        run("curl -sL https://github.com/cilium/cilium-cli/releases/latest/download/cilium-linux-amd64.tar.gz | tar xz")
        run("./eksctl create cluster -f eks-config.yaml --without-nodegroup")
        run(f"./cilium install --set kubeProxyReplacement=true --set k8sServiceHost=$(./eksctl get cluster --name {name} -o yaml | grep Endpoint: | cut -d'/' -f 3) --set k8sServicePort=443")
        open("eks-config.yaml", "w").write(eks_cluster)
        run(f"./eksctl create nodegroup -f eks-config.yaml")
        run(f"./cilium hubble enable --ui")
        run("./cilium status --wait")
        os.chdir(cwd)