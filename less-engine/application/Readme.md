How to use:

cd to each folder and build the docker image
```
docker build -t lesscompiler:server .
docker build -t lesscompiler:client .
```
Push to docker repository


Deploy the application

```
$ kubectl apply -f client.yaml Deployment.yaml service.yaml

```