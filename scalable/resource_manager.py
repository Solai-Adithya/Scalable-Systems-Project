from signal import SIGTERM
from uuid import RESERVED_FUTURE
from threading import Timer
from flask import Flask, jsonify, request
from instance_factory import InstanceFactory

app = Flask(__name__)

class ResourceManager(object):
    __instance = None
    instanceFactory = InstanceFactory()
    WORKING_INSTANCES = set()
    FailureCount = 0
    CircuitBroken = False
    CooldownTime = 10

    #Circuit Breaker
    def HandleFailure(self):
        self.FailureCount += 1
        if(self.FailureCount > 3):
            self.CircuitBroken = True
            Timer(self.CooldownTime, self.ResetFailureCount).start()

    def ResetFailureCount(self):
        self.FailureCount = 0
        self.CircuitBroken = False

    def __new__(klass):
        if klass.__instance is None:
            #Lazily initializing singleton class
            klass.__instance = super(ResourceManager, klass).__new__(klass)
        return klass.__instance

    def create_instance(self, type):
        cloud = self.instanceFactory.getCloudObject(type)
        success_status, instance_or_error = cloud.create_instance()
        if(success_status==True):
            self.WORKING_INSTANCES.add(instance_or_error)
            self.ResetFailureCount()
        else:
            self.HandleFailure()
        return success_status, instance_or_error

    def delete_instance(self, type, instance_id):
        cloud = InstanceFactory().getCloudObject(type)
        success_status, instance_or_error = cloud.delete_instance(instance_id)
        if(success_status==True):
            self.WORKING_INSTANCES.remove(instance_or_error)
        return success_status, instance_or_error


@app.route('/')
def index():
    return jsonify(success=True, WORKING_INSTANCES=str(ResourceManager().WORKING_INSTANCES))


@app.route('/create_instance')
def create_instance_api():
    type = "DummyCloud"
    if "type" in request.args:
        type = request.args["type"]

    if(ResourceManager().CircuitBroken):
        return jsonify(success=False, error="Circuit Broken, try later.")

    success_status, instance_or_error = ResourceManager().create_instance(type)
    if success_status:
        return jsonify(success=True, instance_id=instance_or_error)
    return jsonify(success=False, error=instance_or_error)


@app.route('/delete_instance')
def delete_instance_api():
    type = "DummyCloud"
    if "type" in request.args:
        type = request.args["type"]

    if "instance_id" not in request.args:
        return jsonify(success=False, error="instance_id not provided")

    instance_id = request.args["instance_id"]
    success_status, instance_or_error = ResourceManager().delete_instance(type, instance_id)
    if success_status:
        return jsonify(success=True, instance_id=instance_or_error)
    return jsonify(success=False, error=instance_or_error)


if __name__ == "__main__":
    app.run(port=4999, debug=True)
