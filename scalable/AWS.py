from cloud_provider import CloudProvider
import boto3

class AWS(CloudProvider):
    
    def __init__(self) -> None:
        self.ec2 = boto3.resource('ec2')

    def create_instance(self):
        print("Attempting to create AWS Instance")

        try:
            instances = self.ec2.create_instances(
                ImageId='ami-0b0ea68c435eb488d',
                MinCount=1,
                MaxCount=1,
                InstanceType='t2.micro',
                KeyName='ec2-keypair'
            )
            #Returns if creation was successful, instance id and dictionary of instances
            return True, instances[0].id
        except Exception as e:
            return False, e

    def delete_instance(self, instanceID):
        try:
            self.ec2.instances.filter(InstanceIds = [instanceID]).terminate()
            return True, instanceID
        except Exception as e:
            return False, e

