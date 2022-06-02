from cloud_provider import CloudProvider

class AWS(CloudProvider):

    def create_instance(self):
        print("Attempting to create AWS Instance")

        #Returns if creation was successful, instance id and dictionary of instances
        return True, 100

    def delete_instance(self, instanceID):
        print("Attempting to delete AWS instance ID: ", instanceID)
        return True, 100

