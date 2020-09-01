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
  - [KubeVirt](#KubeVirt)
  - [kubevirt-py](#kubevirt-py)
- [Quick Start](#quick-start)
  - [Create a Configmap that is based on a Config of kubernetes cluster](#Create-a-Configmap-that-is-based-on-a-Config-of-kubernetes-cluster)
  - [Create kube5gnfvo ServiceAccount](#Create-kube5gnfvo-ServiceAccount)
  - [Deploy Mysql Database](#Deploy-Mysql-Database)
  - [Deploy kube5gnfvo](#Deploy-kube5gnfvo)
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
kubectl apply -f ovs-cni.yaml
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
kubectl apply -f deployment.yaml
(Please make sure that etcdclusters.etcd.database.coreos.com CRD in Kubernetes has been created)
kubectl apply -f ./
```
### Metrics Server
>Please refer to [Kubernetes Metrics Server Readme](https://github.com/kubernetes-sigs/metrics-server/blob/master/README.md) to deploy metrics server.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/metrics-server/
kubectl apply -f ./
```
### Node Exporter
>Please refer to [Coreos Node Exporter Daemonset](https://github.com/coreos/kube-prometheus/blob/master/manifests/node-exporter-daemonset.yaml) to deploy node exporter.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/
kubectl apply -f prom-node-exporter.yaml
```

### KubeVirt
>Please refer to [KubeVirt Quickstart with Minikube](https://github.com/kubevirt/kubevirt) to deploy KubeVirt.
##### Or follow the instructions
```shell=
cd kube5gnfvo/example/kubevirt/
kubectl apply -f ./
```

### kubevirt-py
>Please refer to [KubeVirt Quickstart with Minikube](https://github.com/kubevirt/client-python) to deploy kubevirt-py.
##### Or follow the instructions
```shell=
cd kube5gnfvo/client-python/
python setup.py install --user
```

## Quick Start
This section explains an exmaple deployment of Kube5GNfvo in Kubernetes. Required YAML files can be found in directory.
### Create a Configmap that is based on a Config of kubernetes cluster

#### copy the content into a pure text editor such as Notepad firs
```shell=
cat ~/.kube/config
```
#### And copy it from there into kube5gnfvo-configmap.yaml
```shell=
cat <<EOF >./kube5gnfvo-configmap.yaml

apiVersion: v1
kind: ConfigMap
metadata:
  name: kube5gnfvo-config
data:
  config: |
    ...
      'Here!'
    ...

EOF

kubectl apply -f kube5gnfvo-configmap.yaml
```

### Create kube5gnfvo ServiceAccount
```shell=
cat <<EOF >./kube5gnfvo-sa.yaml
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

kubectl apply -f kube5gnfvo-sa.yaml
```

### Deploy Mysql Database
```shell=
cat <<EOF >./kube5gnfvo-mysql.yaml
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
    name: kube5gnfvo-mysql
spec:
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    type: DirectoryOrCreate
    path: /mnt/kube5gnfvo-mysql
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
  selector:
    matchExpressions:
    - key: name
      operator: In
      values: ["kube5gnfvo-mysql"]
---
apiVersion: v1
kind: Service
metadata:
  name: kube5gnfvo-mysql
spec:
  ports:
  - port: 3306
  selector:
    app: kube5gnfvo-mysql
---
apiVersion: v1
kind: ConfigMap
metadata:
  name: mysql-initdb-config
data:
  initdb.sql: |
    CREATE DATABASE kube5gnfvo;
EOF

kubectl apply -f kube5gnfvo-mysql.yaml
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
      - image: free5gmano/kube5gnfvo-stage2
        name: kube5gnfvo
        env:
        - name: DATABASE_PASSWORD
          value: "password"
        - name: DATABASE_HOST
          value: "kube5gnfvo-mysql"
        - name: DATABASE_PORT
          value: "3306"
        command: ["/bin/sh","-c"]
        args: ['python3 manage.py migrate && python3 manage.py runserver 0:8000']
        ports:
        - containerPort: 8000
          name: kube5gnfvo
        volumeMounts:
        - name: kube5gnfvo-vnf-package
          mountPath: /root/NSD
          subPath: NSD
        - name: kube5gnfvo-vnf-package
          mountPath: /root/VnfPackage
          subPath: VnfPackage
      volumes:
      - name: kube5gnfvo-vnf-package
        persistentVolumeClaim:
          claimName: kube5gnfvo-pvc
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
---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: kube5gnfvo-pvc
  namespace: default
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 20Gi
  selector:
    matchExpressions:
    - key: name
      operator: In
      values: ["kube5gnfvo"]
---
apiVersion: v1
kind: PersistentVolume
metadata:
  name: kube5gnfvo-pv
  labels:
    name: kube5gnfvo
spec:
  capacity:
    storage: 20Gi
  accessModes:
    - ReadWriteOnce
  hostPath:
    type: DirectoryOrCreate
    path: /mnt/kube5gnfvo
EOF

kubectl apply -f kube5gnfvo.yaml
```

### Example deployments
#### Testing kube5gnfvo
##### POSTMAN
We use POSTMAN to send request to API server. You can download at [here](https://www.postman.com/downloads/).
##### Create NS instance
>Compress files
````
Under kube5gnfvo/example/free5gcv1
````
You will see two directories, ns and Vnfpackage.
Zip ns directory into ns.zip. In  kube5gnfvo/example/free5gcv1/Vnfpackage, you will see seven directories, zip each of them into .zip file directly.
Now the file structure shown as below:
````
kube5gnfvo/example/free5gcv1
|--ns
|--ns.zip
|--vnfpackage
   |--amf
   |--hss
   |--mongodb
   |--pcrf
   |--smf
   |--upf
   |--webui
   |--amf.zip
   |--hss.zip
   |--mongodb.zip
   |--pcrf.zip
   |--smf.zip
   |--upf.zip
   |--webui.zip
````

>Create and upload VNF packages
````
Under kube5gnfvo/example/free5gcv1
````
* Create VNF packages
We send request to API server in "POST" method.
1. You can modify following URL, replace <your server IP> as your IP address, and fill it in the request URL column.
````
http://<your server IP>:30888/vnfpkgm/v1/vnf_packages/
````
![](https://i.imgur.com/qiqi1cS.png)

Send request to server, you will receive server response "201 Created".

* Upload VNF packages
On the previous step, server will respone an id number(see the figure shown below, the red box)
![](https://i.imgur.com/ziatPPT.png)

2. Create a new request in "PUT" method. 
Modify following URL, replace <your server IP> as your IP address; <id> as we got in last figure.
````
http://<your server IP>:30888/vnfpkgm/v1/vnf_packages/<id>/package_content/
````
![](https://i.imgur.com/HxQUc2o.png)

3. Modify the headers of the request. Add two key-value, "Accept-application/zip" and "Accept-application/json" as following figure shown.
![](https://i.imgur.com/jNxaDYw.png)

4. Modify the body of the request. 
In "form-data" format, we add one key-value: "file" is our key and seven .zip files we compressed under /vnfpackages directory is our "value".
Remenber to select value type as "file" then you can choose .zip file as your value. To select value type you can find the menu as shown in figure(red box).
In each request we will upload only "one" file.

![](https://i.imgur.com/vceOJpu.png)

5. Send the request to server, you will get response "202 Accepted".

6. Repeat step 1 to step 4, each time replace one .zip file under /vnfpackages directory. Not until upload seven .zip file will you go to next step (step 7).

>Create ns descriptor

7. Create a new request in "POST" method.
Modify following URL, replace <your server IP> as your IP address.
````
http://<your server IP>:30888/nsd/v1/ns_descriptors/
````
Send request to server. You will receive server response "201 Created", and an id number as shown in following figure (red box).
![](https://i.imgur.com/YJXk7WE.png)

>Create and upload ns descriptor

8. Create a new request in "PUT" method.
Modify following URL, replace <your server IP> as your IP address; <id> as we got in last figure.
````
http://<your server IP>:30888/nsd/v1/ns_descriptors/<id>/nsd_content/
````

9. Modify the headers of the request. Add two key-value, "Accept-application/zip" and "Accept-application/json" as following figure shown.
![](https://i.imgur.com/YUDWd6B.png)

10. Modify the body of the request. In "form-data" format, we add one key-value: "file" is our key and "value" is our ns.zip file we comressed before. Also remenber to select type of value as "file"(shown in following figure, red box).
![](https://i.imgur.com/afmys1R.png)
Send the request to server, you will receive server response "202 Accepted".

> Create and instantiate ns instance

11. Create a new request in "POST" method.
Modify following URL, replace <your server IP> as your IP address.
````
http://<your server IP>:30888/nslcm/v1/ns_instances/
````

12. Modify the body of the request. In "raw, JSON" format, type in following JSON file.
````
{
    "nsdId": "2116fd24-83f2-416b-bf3c-ca1964793acb",
    "nsName": "String",
    "nsDescription": "String"
}
````
![](https://i.imgur.com/49GufwZ.png)
Send the request to server, you will receive server response "201 Created", and body of response in JSON format. Retain the response, we will use them in next step.

13. Create a new request in "POST" method.
Modify following URL, replace <your server IP> as your IP address; <id in red box> as we got in last response(as following figure shown, in red box).
````
http://<your server IP>:30888/nslcm/v1/ns_instances/<id in red box>/instantiate/
````
![](https://i.imgur.com/Q58u21n.png)

14. In request body, we used "raw, JSON" format.You can fill in the body as following.
````
{
    "vnfInstanceData":[
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        },
        {
            "vnfInstanceId": "<id in second layer>",
            "vnfProflieId": "String"
        }
    ]
}
````
For "vnfInstanceId" fields, you can get them in previous response. The response in JSON format, we used ID in second layer as vnfInstanceId. The following is the JSON structure of response to show how we use in vnfInstanceId. You can also see the blue box in previous figure as example.
````
{
    "id": "ce76d430-f8d8-4598-9229-cdae44ab9f32",
    "vnffgInfo": [],
    "vnfInstance": [
        {
            "id": "<vnfInstanceId we look for>",
            "vnfInstanceName": "2116fd24-83f2-416b-bf3c-ca1964793smf-iqfuvhakgw",
            ......
        },
        {
            "id": "<vnfInstanceId we look for>",
            "vnfInstanceName": "2116fd24-83f2-416b-bf3c-ca19647webui-augxvnqoyw",
            ......
        },
        ......
}
````
Send the request to server, you will receive server response "202 Accepted".
