# Term Project - Data Dive
Term project repository for CMPT 756.  
Building, scaling and observing a working distributed application.

## 💻 Group Details
**Team Name:** Data Dive

**Group Members:**
* Geethika Payyaula
* Viddhi Lakhwara
* Saurabh Singh
* Sambhav Rakhe
* Aman Purohit

## Structure
**Important Directories**
* `cluster`: Configuration files for the cluster<br>
* `db`: Database service<br>
* `gatling`: Scala scripts used by Gatling to generate test load on the application<br>
* `loader`: Loader service used to insert data into the DynamoDB service<br>
* `logs`: Where logs are stored<br>
* `s1`: User service<br>
* `s2`: Music service<br>
* `s3`: Playlist service<br>
* `tools`: For quick scripts that are useful in make-files<br>
---
### Instantiate the template files

#### Fill in the required values in the template variable file

Copy the file `cluster/tpl-vars-blank.txt` to `cluster/tpl-vars.txt`
and fill in all the required values in `tpl-vars.txt`.  These include
things like your AWS keys, your GitHub signon, and other identifying
information.  See the comments in that file for details. Note that you
will need to have installed Gatling
(https://gatling.io/open-source/start-testing/) first, because you
will be entering its path in `tpl-vars.txt`.

#### Instantiate the templates

Once you have filled in all the details, run

~~~
$ make -f k8s-tpl.mak templates
~~~

This will check that all the programs you will need have been
installed and are in the search path.  If any program is missing,
install it before proceeding.

The script will then generate makefiles personalized to the data that
you entered in `clusters/tpl-vars.txt`.

**Note:** This is the *only* time you will call `k8s-tpl.mak`
directly. This creates all the non-templated files, such as
`k8s.mak`.  You will use the non-templated makefiles in all the
remaining steps.

The application incorporates four services (User Service, Music Service, Playlist Service, Db Service):

The microservice design
Service	Short name	Purpose	Location
Users	S1	List of users	Your Kubernetes cluster on AWS
Music	S2	Lists of songs and their artist	Your Kubernetes cluster on AWS
Database	DB	Interface to key-value store	Your Kubernetes cluster on AWS
DynamoDB	(None)	Key-value store	Service managed by Amazon

---
### Start your AWS EKS cluster

To start the container, run the followimg command:
~~~
$ tools/shell.sh
~~~
~~~
/home/k8s# make -f eks.mak start
~~~
This is a slow operation, often taking 10–15 minutes. If you review eks.mak, this is the command that was used (some parameters may vary):
~~~
/home/k8s# eksctl create cluster --name aws756 --version 1.21 --region us-west-2 --nodegroup-name worker-nodes --node-type t3.medium --nodes 2 --nodes-min 2 --nodes-max 2 --managed
~~~
You can see where parameters have been used to allow for easy tailoring. At the completion of this command (typically 10-15 minutes), you will have a barebone k8s cluster comprising some master nodes and 2 worker nodes (each of which is an EC2 instance). (The nodes are specified by the tail --node-type t3.medium --nodes 2 --nodes-min 2 --nodes-max 2.)

The makefiles included set **aws756** context names for **AWS EKS**	cloud vendor:

We set the context name and nnamespce using the following commands:
~~~
/home/k8s# kubectl config use-context aws756
~~~
~~~
/home/k8s# kubectl create ns c756ns
~~~
~~~
/home/k8s# kubectl config set-context aws756 --namespace=c756ns
~~~
To reduce cost, you can either delete the cluster entirely or delete the nodegroup.
~~~
/home/k8s# make -f eks.mak stop
~~~
Deleting the nodegroup does not harm the cluster. If anything, the design of Kubernetes supports and anticipates the removal of computing resources.

To delete the nodegroup of your cloud cluster:
~~~
/home/k8s#  make -f VENDOR.mak down
~~~
To recreate the node-group of your cloud cluster:
~~~
/home/k8s#  make -f VENDOR.mak up<br>
---
~~~
### Deploying your Application
We will need to build the containers and push them to the container registry. Please save your **ghcr(github container registry)** token in **ghcr.io-token.txt** in the cluster folder. 
Build your images with (cri short for container registry images):
Finally, there is one manual step left before the system can come up auto-magically: to switch your container repositories to public access. (This is a simplification for the purpose of this course.)
~~~
/home/k8s# make -f k8s.mak cri
~~~
Refer to GitHub’s documentation to [set public access on your container repositories](https://docs.github.com/en/packages/guides/configuring-access-control-and-visibility-for-container-images#configuring-visibility-of-container-images-for-your-personal-account)
**Deploying the services**
*S1: User Service
*S2: Music Service
*S1: Playlist Service
*DB: The database service, providing persistent storage to the two higher-level services, S1 and S2.
*DynamoDB: An Amazon service, called by DB to actually store the values.
*Gateway: A link between S1 and S2 and the external world, such as your machine.
To run this, we first need to start the gateway, database, and music, user and playlist services. We can do that with a single call:
~~~
/home/k8s# make -f k8s.mak gw db s2 s1 s3
~~~
or 
~~~
/home/k8s# make -f k8s.mak provision
~~~
To complete setting up the music service, we need to initialize DynamoDB and load it with initial data:
~~~
/home/k8s# make -f k8s.mak loader
~~~
This step builds and pushes another image (cmpt756loader) to ghcr.io. Return to your GitHub Packages tab and set the access for this new image to public as before.

**Ensure AWS DynamoDB is accessible/running**

Regardless of where your cluster will run, it uses AWS DynamoDB
for its backend database. Check that you have the necessary tables
installed by running
~~~
$ aws dynamodb list-tables
~~~
The resulting output should include tables `User`, `Music` and `Playlist`.
To create/delete these tables by way of AWS’ CloudFormation (AWS’ IaC technology):
~~~
# create a stack that encapsulate the 3 tables
$ aws cloudformation create-stack --stack-name <SomeStackName> --template-body file://path/to/cluster/cloudformationdynamodb.json 
# delete the stack
$ aws cloudformation delete-stack --stack-name <SomeStackName>
~~~
To test that all these pieces are now working, get the **EXTERNAL-IP** using the command:
~~~
/home/k8s# kubectl -n istio-system get service istio-ingressgateway | cut -c -140
~~~
The External-IP would be something like: a844a1e4bb85d49c4901affa0b677773-127853909.us-west-2.elb.amazonaws.com 
Now we can test the microservices using Postman:
Select the correct Request Method and enter the url as:
~~~
https://External-IP/api/v1/playlist/playlist_id
~~~
We will get a valid response from the DynamoDB table for that playlist_id.
We can similarly test for User Service and Music Service.

---
### Load Testing our services using Gatling and Grafana
**Print the Grafana URL**
Test that all the steps worked by printing the URL of the Grafana dashboard (you will only get one of the following lines, depending upon where your cluster is running).

If using Minikube, bring up the gateway (minikube tunnel where you have sudo rights) or set up an appropriate port-forwarding tunnels (kubectl -n c756ns port-forward pod/<podname> <port-ext>:<port-int>).
~~~
$ make -f k8s.mak grafana-url
http://35.197.120.255:3000/                                                          # Sample output for most cloud providers
http://a3a64fbacc7114a028faa18b4a710f87-1707422240.us-west-2.elb.amazonaws.com:3000/ # Sample output for Amazon
~~~
Copy this URL and paste it into your browser. You will see the Grafana signon page.

Overview of Grafana dashboard
Sign on to Grafana with the following parameters:
~~~
User: admin
Password: prom-operator
~~~
After signon, you will see the Grafana home screen. Navigate to our dashboard by hovering on the “Dashboards” icon on the left:
![alt text](https://github.com/scp756-221/term-project-data-dive/blob/data-dive-saurabh/visualizations/Grafana-home-page-highlighting-dashboards-menu-item.png)
  
Select “Browse” from the menu. This will bring up a list of dashboards. Click on c756 transactions (it should be at or near the top of the list).
With this, Graffana Dashboard is added for monitoring the load on the services.

## Giving our services an initial load
Now we will begin to send load to the system, simulating user interactions.
To create this load, you will use Gatling via an image that has been prepared for you: `ghcr.io/scp-2021-jan-cmpt-756/gatling:3.4.2.`) (The source Dockerfile is available [here](https://github.com/tedkirkpatrick/kubernetes-testbed/tree/master/e-k8s/tools/gatling).)

**Start Gatling**:
Gatling is a sophisticated tool that allows you to define scenarios of user behaviour, using a programming language derived from Scala. You then run Gatling, specifying how many simulated users will follow each scenario.

We have provided three scenarios (Gatling calls them simulations) for you. The source code is supplied at `gatling/simulations/proj756/ReadTables.scala`:

*`ReadUserSim`: Call `s1` to read a user, then wait 1 s before trying again
*`ReadMusicSim`: Call `s2` to read a music entry, then wait 1 s before trying again
*`ReadPlaylistSim`: Call `s3` to read a music entry, then wait 1 s before trying again
The simulations uses three parameters:

`CLUSTER_IP` - the DNS name of your cluster
`USERS` - the number of users to simulate
`SIM_NAME` - selects either `ReadUserSim`, `ReadMusicSim` or `ReadPlaylistSim` to choose between the microservices.
Each simulation runs in an infinite loop until it is stopped (docker container stop). (There is also a ‘bulk kill’ script tools/kill-gatling.sh.)

To start Gatling, create a script `gatling-1-music.sh` that contains the following:
~~~  
#!/usr/bin/env bash
docker container run --detach --rm \
  -v ${PWD}/gatling/results:/opt/gatling/results \
  -v ${PWD}/gatling:/opt/gatling/user-files \
  -v ${PWD}/gatling/target:/opt/gatling/target \
  -e CLUSTER_IP=`tools/getip.sh kubectl istio-system svc/istio-ingressgateway` \
  -e USERS=1 \
  -e SIM_NAME=ReadMusicSim \
  --label gatling \
  ghcr.io/scp-2021-jan-cmpt-756/gatling:3.4.2 \
  -s proj756.ReadMusicSim
~~~
 
To stop gatling, use `tools/kill-gatling.sh`. Note that this scripts stops all accumulated/running simulations.  

View the effects on the dashboard
Return to the Grafana dashboard. Now that we have a light load on the system, all the panels with the exception of “Errors per second” should have data. For such a light load, we will not have any errors, so this is expected.

  
### Prometheus
Print out Prometheus URL for the cluster by running:
~~~  
$ make -f k8s.mak prometheus-url
http://20.48.136.216:9090/
~~~
![alt text](https://scp756-221.github.io/course-site/g2-prom/prometheus-new-ui.png)
