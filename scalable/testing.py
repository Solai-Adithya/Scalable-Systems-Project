import requests

while(True):
    inp = input("Enter the port/address to which request to be made: ")
    res = requests.get("http://localhost:" + str(inp))
    if res.ok:
        print(res.json())
    else:
        print(res.text)

