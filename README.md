# Kube5GNfvo

## Table of Contents

- [Kube5GNfvo](#Kube5GNfvo)
- [Prerequisites](#prerequisites)
  - [Kubernetes](#Kubernetes)
  - [Multus](#Multus)
  - [OpenvSwitch](#OpenvSwitch)
  - [OVS-CNI](#OVS-CNI)
  - [Etcd Operator](#Etcd-Operator)
  - [Metrics Server](#Metrics-Server)
  - [Node Exporter](#Node-Exporter)
- [Quick Start](#quick-start)
  - [Create kube5gnfvo ServiceAccount](#Create-kube5gnfvo-ServiceAccount)
  - [Deploy Mysql Database](#Deploy-Mysql-Database)
  - [Example deployments](#example-deployments)
    - [Testing kube5gnfvo](#Testing-kube5gnfvo)

### Kubernetes
Please refer to [Bootstrapping clusters with kubeadm](https://kubernetes.io/docs/setup/production-environment/tools/kubeadm/install-kubeadm/) to install Kubernetes.
>Using Kubernetes version: v1.15.3

##### on ubuntu
```shell=
apt-get install -y kubelet=1.15.3-00 kubeadm=1.15.3-00 kubectl=1.15.3-00 --allow-downgrades
```

### Multus
>Please refer to [Multus Quickstart Installation Guide](https://github.com/intel/multus-cni#quickstart-installation-guide) to install Multus.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/
kubectl apply -f multus-daemonset-pre-1.16.yml
```

### OpenvSwitch
>Please refer to [Open vSwitch Installation Guide](http://docs.openvswitch.org/en/latest/intro/install/#) to install OpenvSwitch.
##### Or follow the instructions
```shell=
apt install openvswitch-switch -y
ovs-vsctl add-br br1
```
### OVS-CNI
>Please refer to [Kubevirt OVS CNI](https://github.com/kubevirt/ovs-cni) to install ovs-cni.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/
kubectl apply -f ovs-cni.yml
```
##### Create a NetworkAttachmentDefinition
```shell=
cat <<EOF >./ovs-net-crd.yaml
apiVersion: "k8s.cni.cncf.io/v1"
kind: NetworkAttachmentDefinition
metadata:
  name: ovs-net
  annotations:
    k8s.v1.cni.cncf.io/resourceName: ovs-cni.network.kubevirt.io/br1
spec:
  config: '{
      "cniVersion": "0.3.1",
      "type": "ovs",
      "bridge": "br1"
    }'
EOF
kubectl apply -f ovs-net-crd.yaml
```

### Etcd Operator
>Please refer to [Coreos Etcd Operator Readme](https://github.com/coreos/etcd-operator/blob/master/README.md) to install etcd cluster.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/etcd-cluster/rbac/
./create_role.sh
cd ..
kubectl apply -f ./
```
### Metrics Server
>Please refer to [Kubernetes Metrics Server Readme](https://github.com/kubernetes-sigs/metrics-server/blob/master/README.md) to deploy metrics server.
##### Or follow the instructions
```shell=
git clone https://github.com/kubernetes-incubator/metrics-server
cd metrics-server/deploy/kubernetes/

vim metrics-server-deployment.yaml

...
containers:
...
  command:
  - /metrics-server
  - --kubelet-insecure-tls
  - --kubelet-preferred-address-types=InternalIP
...
kubectl apply -f ./
```
### Node Exporter
>Please refer to [Coreos Node Exporter Daemonset](https://github.com/coreos/kube-prometheus/blob/master/manifests/node-exporter-daemonset.yaml) to deploy node exporter.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/
kubectl apply -f prom-node-exporter.yaml
```

## Quick Start
This section explains an exmaple deployment of Kube5GNfvo in Kubernetes. Required YAML files can be found in directory.

### Create kube5gnfvo ServiceAccount
```shell=
cat <<EOF >./service-account-agent.yaml
---
kind: ClusterRoleBinding
apiVersion: rbac.authorization.k8s.io/v1beta1
metadata:
  name: kube5gnfvo
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin
subjects:
- kind: ServiceAccount
  name: kube5gnfvo
  namespace: default
---
apiVersion: v1
kind: ServiceAccount
metadata:
  name: kube5gnfvo
EOF

kubectl apply -f service-account-agent.yaml
```

### Deploy Mysql Database
```shell=
cat <<EOF >./mysql-agent.yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube5gnfvo-mysql
spec:
  strategy:
    type: Recreate
  selector:
    matchLabels:
      app: kube5gnfvo-mysql
  template:
    metadata:
      labels:
        app: kube5gnfvo-mysql
    spec:
      containers:
      - image: mysql:5.6
        name: kube5gnfvo-mysql
        env:
        - name: MYSQL_ROOT_PASSWORD
          value: password
        ports:
        - containerPort: 3306
          name: mysql
        volumeMounts:
        - name: kube5gnfvo-mysql
          mountPath: /var/lib/mysql
        volumeMounts:
        - name: mysql-initdb
          mountPath: /docker-entrypoint-initdb.d
      volumes:
      - name: kube5gnfvo-mysql
        persistentVolumeClaim:
          claimName: kube5gnfvo-mysql
      volumes:
      - name: mysql-initdb
        configMap:
          name: mysql-initdb-config
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: kube5gnfvo-mysql
  labels:
    type: local
spec:
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    path: "/mnt/data"
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kube5gnfvo-mysql
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
---
apiVersion: v1
kind: Service
metadata:
  name: kube5gnfvo-mysql
spec:
  type: NodePort
  ports:
  - port: 3306
    nodePort: 30036
  selector:
    app: kube5gnfvo-mysql
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-initdb-config
data:
  initdb.sql: |
    CREATE DATABASE kube5gmano;
EOF

kubectl apply -f mysql-agent.yaml
```

### Deploy kube5gnfvo
```shell=
cat <<EOF >./kube5gnfvo.yaml
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: kube5gnfvo
spec:
  replicas: 1
  selector:
    matchLabels:
      app: kube5gnfvo
  template:
    metadata:
      labels:
        app: kube5gnfvo
    spec:
      serviceAccountName: kube5gnfvo
      containers:
      - image: free5gmano/kube5gnfvo
        name: kube5gnfvo
        env:
        - name: DATABASE_PASSWORD
          value: "password"
        - name: DATABASE_HOST
          value: "10.0.1.203"
        - name: DATABASE_PORT
          value: "30036"
        command: ["/bin/sh","-c"]
        args: ['python3 manage.py migrate && python3 manage.py runserver 0:8000']
        ports:
        - containerPort: 8000
          name: kube5gnfvo
---
apiVersion: v1
kind: Service
metadata:
  name: kube5gnfvo
spec:
  type: NodePort
  ports:
  - port: 8000
    nodePort: 30888
  selector:
    app: kube5gnfvo
EOF

kubectl apply -f kube5gnfvo.yaml
```