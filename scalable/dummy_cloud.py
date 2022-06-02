
import multiprocessing
import os
import sys
from signal import SIGTERM
from cloud_provider import CloudProvider

lock = multiprocessing.Lock()
manager = multiprocessing.Manager()
WORKING_INSTANCES = manager.dict()
GLOBAL_VARS = manager.dict()

class DummyCloud(CloudProvider):

    def __init__(self):
        global GLOBAL_VARS
        global lock

        lock.acquire()
        GLOBAL_VARS["CURRENT_PORT"] = 5002
        lock.release()

    def create_instance(self):
        print("Attempting to create dummy Instance")
        global lock
        global GLOBAL_VARS
        global WORKING_INSTANCES

        try:
            fork_id = os.fork()
        except:
            return False, "Fork failed!"

        if fork_id > 0:
            lock.acquire()
            instance_id = "localhost:" + str(GLOBAL_VARS["CURRENT_PORT"])
            lock.release()
            return True, instance_id
        else:
            print("Child process and id is : ", os.getpid())
            process_pid = os.getpid()

            lock.acquire()
            current_port = GLOBAL_VARS["CURRENT_PORT"]
            print("Start an instance_port: ", current_port)

            # Instead start a new python app, TODO
            # os.system("python instance.py " + str(current_port))
            instance_id = "localhost:" + str(current_port)
            WORKING_INSTANCES[instance_id] = process_pid
            GLOBAL_VARS["CURRENT_PORT"] += 1
            lock.release()

            sys.argv = ["instance.py", str(current_port)]
            script = open("instance.py")
            code = script.read()
            # set the arguments to be read by script.py
            exec(code)

            return True, instance_id

    def delete_instance(self, instance_id):
        print("Attempting to delete dummy instance ID: ", instance_id)
        global WORKING_INSTANCES
        global lock

        lock.acquire()
        if instance_id not in WORKING_INSTANCES:
            lock.release()
            return False, "No such instance exists!"

        instance_pid = WORKING_INSTANCES[instance_id]
        os.kill(instance_pid, SIGTERM)
        WORKING_INSTANCES.pop(instance_id)
        lock.release()

        return True, instance_id

