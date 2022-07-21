# Design Patterns for Scalable Systems Project
A simulation of a job submission & processing system using related design patterns that help in making the systems maintainable and more reliable.


### Design patterns implemented
1. Factory Design Pattern - Creates a specific kind of object from that factory.
2. Resource Management Design Pattern - Used to manage the instances/resources on AWS or Any other cloud platform. Mainly used to create EC2 instances.
3. Proxy Design Pattern - Actual worker substituted with a proxy which handles communication with actual instance.
4. Heart Beat Pattern - Worker proxy makes heart beat requests at certain time interval
5. Circuit Breaker Design Pattern - In case of failure, the circuit breaker denies requests until stability is achieved, so that a backlog of requests is not created.

