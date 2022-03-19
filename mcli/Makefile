# Makefile for standalone Music service (S2)

VER=v0.8

# TODO: Define ARCH on an M1 Mac to possibly force the use of Rosetta2.
#ARCH=--platform amd64
ARCH=

SERVER=`docker inspect s2 --format '{{.NetworkSettings.IPAddress}}'`
PORT=30001

build-mcli:
	docker image build $(ARCH) -f Dockerfile -t mcli:$(VER) .

run-mcli:
	docker container run $(ARCH) -it --rm --name mcli mcli:$(VER) python3 mcli.py $(SERVER) $(PORT)
