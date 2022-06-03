from time import sleep
from flask import Flask, jsonify, request
import os
import requests
import multiprocessing

app = Flask(__name__)

manager = multiprocessing.Manager()

# stores the list of instances that are currently working
WORKING_INSTANCES = manager.dict()
WORKING_WORKERS = manager.dict()
lock = multiprocessing.Lock()

class Worker:
    def test_instance(self, instance_url):
        ''' Makes a get request to the instance url, and return True if it is working '''
        print("Testing instance url: ", instance_url)

        try:
            requests.get(instance_url)
        except requests.exceptions.InvalidSchema:
            try:
                requests.get("http://" + str(instance_url))
            except:
                return False

        except requests.ConnectionError:
            return False

        return True

    def handle_instance_failure(self, instance_id):
        # check if it is in the working instances or not
        # If it is, there is a failure
        # If not, it has been deleted by the job_manager already, nothing to
        global WORKING_INSTANCES
        global WORKING_WORKERS
        global lock

        lock.acquire()
        print("checking instance failure", instance_id)
        # print("WORKING INSTANCES", WORKING_INSTANCES)

        if instance_id not in WORKING_INSTANCES:
            print("Worker should be completed, instance already deleted")
            WORKING_WORKERS.pop(instance_id)
            lock.release()
        else:
            print("Instance with id", instance_id, " failed")
            WORKING_INSTANCES.pop(instance_id)
            print("Instane has been failed, create a new instance!")

            WORKING_WORKERS.pop(instance_id)
            lock.release()

            # Create a new instance by requesting the own server only
            res = requests.get('http://localhost:4998/create_instance')
            if res.ok:
                print(res.text)
            else:
                print("Response failed may be!")


    def create_worker(self, instance_id):
        global WORKING_INSTANCES
        global WORKING_WORKERS
        global lock

        ''' Returns True if creation of worker proxy is successfull '''
        try:
            fork_id = os.fork()
        except:
            return False

        if fork_id > 0:
            lock.acquire()
            WORKING_WORKERS[instance_id] = True
            lock.release()

            return True
        else:
            print("Child process and id is : ", os.getpid())

            sleep(5)  # Start checking only after 10 seconds
            # TODO, add atleast one call before checking
            # Now we will keep making some requests
            while True:
                if not self.test_instance(instance_id):
                    # Worker with instance_id failed
                    lock.acquire()
                    print("WORKING INSTANCES", WORKING_INSTANCES)
                    print("WORKING WORKERS", WORKING_WORKERS)
                    lock.release()
                    break
                else:
                    print("Instance ", instance_id, " working properly :)")
                sleep(5)

            print("Worker ", instance_id, " completed or failed")
            self.handle_instance_failure(instance_id)
            exit()  # End the forked process here only




def create_instance_by_id(instance_id):
    global WORKING_INSTANCES
    global lock

    # Same as create instance, but is creates the instance
    # with the provided instance id
    worker_object = Worker()
    if not worker_object.create_worker(instance_id):
        return False, "Worker Creation Failed!"

    lock.acquire()
    WORKING_INSTANCES[instance_id] = True
    lock.release()

    print("Created instance with provided instance id", instance_id)
    return True, instance_id


def create_instance():
    # 1. Will make a request to resource manager
    # 2. Update WORKING_INSTANCES
    # 3. Creates a Worker
    # Returns a tuple(Success_Status, instance_id or error)
    global WORKING_INSTANCES
    global lock

    res = requests.get("http://localhost:4999/create_instance")
    if res.ok:
        res_data = res.json()
        print("Create Instance from resource manager data: ", res_data)
        if not res_data["success"]:
            return False, res_data["error"]

        instance_id = res_data["instance_id"]

        worker_object = Worker()
        if not worker_object.create_worker(instance_id):
            return False, "Worker Creation Failed!"

        lock.acquire()
        WORKING_INSTANCES[instance_id] = True
        lock.release()

        print("Created instance with new instance id", instance_id)
        return True, instance_id

    return False, "Requests Error"



def delete_instance(instance_id):
    # Will make a request to resource manager
    # 2. Update the WORKING_INSTANCES
    # 3. Worker will be already deleted as it will throw
    # Returns a tuple(Success_Status, instance_id or error)
    global WORKING_INSTANCES
    global lock

    lock.acquire()
    WORKING_INSTANCES.pop(instance_id)
    lock.release()
    # TODO, make an API call to resource manager to delete the instance

    res = requests.get("http://localhost:4999/delete_instance?instance_id=" + str(instance_id))
    if res.ok:
        res_data = res.json()
        print("Delete Instance from resource manager data: ", res_data)
        print("res_Data", res_data)

    print("Removed instance with instance id", instance_id)
    return True, instance_id


@app.route('/')
def index_page():
    global WORKING_INSTANCES
    global WORKING_WORKERS

    ''' Returns the list of working instances '''
    return jsonify(WORKING_INSTANCES=str(WORKING_INSTANCES), WORKING_WORKERS=str(WORKING_WORKERS))


@app.route('/test_instance')
def test_instance_api():
    if "instance_url" not in request.args:
        return jsonify(success=False, error="instance_url not provided")

    instance_url = request.args["instance_url"]

    response = "Request failed to " + \
        str(instance_url) + ", Instance is not working!"
    worker_object = Worker()
    if  worker_object.test_instance(instance_url):
        response = "Successful Request " + \
            str(instance_url) + ", Instance is working!"

    return jsonify(success=True, response=response)


@app.route('/create_instance')
def create_instance_api():
    # Make a request to the resource manager to create an instance
    # and then start the worker proxy that looks over to that instance

    success_status, instance_or_error = create_instance()
    if success_status:
        return jsonify(success=True, instance_id=instance_or_error)

    return jsonify(success=False, error=instance_or_error)


@app.route('/delete_instance')
def delete_instance_api():
    if "instance_id" not in request.args:
        return jsonify(success=False, error="instance_id not provieded!")
    instance_id = request.args["instance_id"]

    # # Make a request to the resource manager to delete an instance
    success_status, instance_or_error = delete_instance(instance_id)
    if success_status:
        return jsonify(success=True, instance_id=instance_or_error)

    return jsonify(success=False, error=instance_or_error)


@app.route('/create_worker')
def create_worker_api():
    if "instance_id" not in request.args:
        return jsonify(success=False, error="instance_id not provieded!")
    instance_id = request.args["instance_id"]
    print(instance_id)

    worker_object = Worker()
    if worker_object.create_worker(instance_id):
        return jsonify(success=True, created=True)
    else:
        return jsonify(success=False, error="Worker creation failed!")


@app.route('/test/create_instances')
def test_create_instances_api():
    # Tests our logic and code by creating three instances
    # localhost: 5001, 5002, 5003, ensure they are already
    # running somewhere, and then test the failure
    instances_to_create = ["localhost:5001",
                           "localhost:5002", "localhost:5003", "localhost:5004"]

    for instance_id in instances_to_create:
        create_instance_by_id(instance_id)

    return jsonify(success=True, instances_created=instances_to_create)


if __name__ == "__main__":
    app.run(debug=True, port=4998)
