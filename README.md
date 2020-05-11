# Load Balancer Simulator

Have you ever had to distribute millions of connections between load balancers in sequence?

Have you ever asked "What would happen if I reset load balancers over and over"?

This is a start of a project to answer those questions.


## Usage

Update the `load_balancing.yaml` with you desired tests

````yaml
tests:
  first:
    name: "8 nodes, 5 times" #Can be anything
    loadbalancercount: 140 #number of load balancers for the test
    connections: 6000000 #Number of connections to distribute evenly the first go round
    resetratio: 8 #How many load balancer
    times: 5 #How many times will the simulator run, this will NOT reset the connections, so you are testing just after a reset.
````    
