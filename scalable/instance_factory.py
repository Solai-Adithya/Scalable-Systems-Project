from AWS import AWS
from dummy_cloud import DummyCloud

class InstanceFactory:
    def __init__(self):
        self.AWS_Instance = AWS()
        self.DummyCloud_Instance = DummyCloud()

    def getCloudObject(self, type):
        if(type=="AWS"):
            instance = self.AWS_Instance
        else:
            instance = self.DummyCloud_Instance
            
        return instance
