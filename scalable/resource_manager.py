import os
from signal import SIGTERM
from flask import Flask, jsonify, request
import sys
import multiprocessing

app = Flask(__name__)
manager = multiprocessing.Manager()
WORKING_INSTANCES = manager.dict()
GLOBAL_VARS = manager.dict()
lock = multiprocessing.Lock()


def create_instance():
    # tuple -> success, instance_id or error
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


def delete_instance(instance_id):
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


@app.route('/')
def index():
    global WORKING_INSTANCES

    return jsonify(success=True, WORKING_INSTANCES=str(WORKING_INSTANCES))


@app.route('/create_instance')
def create_instance_api():
    success_status, instance_or_error = create_instance()
    if success_status:
        return jsonify(success=True, instance_id=instance_or_error)
    return jsonify(success=False, error=instance_or_error)


@app.route('/delete_instance')
def delete_instance_api():
    if "instance_id" not in request.args:
        return jsonify(success=False, error="instance_id not provided")

    instance_id = request.args["instance_id"]
    success_status, instance_or_error = delete_instance(instance_id)
    if success_status:
        return jsonify(success=True, instance_id=instance_or_error)
    return jsonify(success=False, error=instance_or_error)


def __init__():
    global GLOBAL_VARS
    global lock

    lock.acquire()
    GLOBAL_VARS["CURRENT_PORT"] = 5002
    lock.release()


if __name__ == "__main__":
    __init__()
    app.run(port=4999)
