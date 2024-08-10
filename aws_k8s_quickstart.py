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
iam:
  withOIDC: true
managedNodeGroups:
- name: workers
  instanceType: {env('AWS_INSTANCE_TYPE' ,'i4i.xlarge')}
  minSize: 3
  maxSize: 6
  desiredCapacity: 3
  privateNetworking: true
  volumeSize: {env('AWS_VOLUME_SIZE', 64)}
  maxPodsPerNode: 600
  amiFamily: Ubuntu2204
  spot: true
"""

def run(cmd: str) -> str:
    print(cmd)
    subprocess.run(cmd, shell=True)

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmpdir:
        os.chdir(tmpdir)
        print(eks_cluster)
        open("eks-config.yaml", "w").write(eks_cluster)
        run("curl -sL https://github.com/eksctl-io/eksctl/releases/latest/download/eksctl_Linux_amd64.tar.gz | tar xz")
        run("curl -sL https://github.com/cilium/cilium-cli/releases/latest/download/cilium-linux-amd64.tar.gz | tar xz")
        run("./eksctl create cluster -f eks-config.yaml --without-nodegroup || ./eksctl upgrade cluster -f eks-config.yaml")
        run(f"./cilium install --set cni.chainingMode=aws-cni --set cni.exclusive=false --set enableIPv4Masquerade=false --set routingMode=native --set endpointRoutes.enabled=true")
        run(f"./eksctl create nodegroup -f eks-config.yaml")
        run("./cilium status --wait")
        run("kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.2/deploy/prerequisite/longhorn-spdk-setup.yaml")
        run("kubectl apply -f https://raw.githubusercontent.com/longhorn/longhorn/v1.6.2/deploy/prerequisite/longhorn-nvme-cli-installation.yaml")
        os.chdir(cwd)