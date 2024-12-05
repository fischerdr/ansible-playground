 ansible-builder build -v3 -t quay.io/ansible/awx-ee # --container-runtime=docker # Is podman by default
 ### build ee environment
 docker buildx create --name test-ee
 docker buildx use test-ee
 ansible-builder create -v3 --output-file=Dockerfile
 docker buildx build --load --tag=test-ee:latest context
 