from hyperledger.client import Client
import json
import datetime
import sys
import time
class HyperledgerClient(object):
	def __init__(self, base_url,mustlogin):
		super(HyperledgerClient, self).__init__()
		self.base_url = base_url
		self.client =  Client(base_url=base_url)
		self.enrollId = "jim"
		print("hyperledger.client version:" + self.client._version)
		if mustlogin:		
			data = {
				"enrollId": self.enrollId,
				"enrollSecret": "6avZQLwcUe9b"
			}
			user = self.client._result(self.client._post(self.client._url("/registrar"),data=json.dumps(data)))
			print(user)

	def deployChainCode(self, chaincode_path, chainCodeArgs):
		deploy = self.execMethod(method="deploy", chaincode_name=None,chaincode_path=chaincode_path, function="init", args=chainCodeArgs)
		return deploy
        '''
		deploy = self.client.chaincode_deploy(chaincode_path=chaincode_path,
									type=1,
									args=chainCodeArgs,
									secure_context=self.enrollId)
									'''
       # print(deploy)
        #self.chaincodeID = str(deploy['result']['message'])
        #return deploy
	def printQueryResult(self, chaincodeID, function ,chainCodeArgs):
		queryResult = self.execMethod(method="query",
					chaincode_name=chaincodeID,
					chaincode_path=None, 
					function=function, args=chainCodeArgs)

		'''
		queryResult = self.client.chaincode_query(chaincode_name=self.chaincodeID, 
										type=1, 
										function="query", 
										args=[target], 
									    secure_context=self.enrollId,  
										metadata=None)
										'''
		#print(queryResult)
		#print("Query: \'"+target+ "\':\'"+  queryResult['result']['message'] +"\'")
		return queryResult
	def printInvokeResult(self, chaincodeID, function ,chainCodeArgs):
            queryResult = self.execMethod(method="invoke", chaincode_name=chaincodeID,chaincode_path=None, function=function, args=chainCodeArgs)
            return queryResult
	def printExecResult(self,command):
		queryResult = self.execMethod(method="query",
								chaincode_name=self.chaincodeID,
								chaincode_path=None, 
								function="exec", args=[command])
		'''
		queryResult = self.client.chaincode_invoke(chaincode_name=self.chaincodeID, 
										type=1, 
										function="invoke", 
										args=[a,b,value], 
										secure_context=self.enrollId,  
										metadata=None)
										'''
		#print("Invoke:\'" + a + "\' transfer "+value+ " to \'" + b + "\'")
		print("exec:" + str(queryResult))
		return queryResult
		#print(self.printQueryResult(command))
	def execMethod(self,method,chaincode_name,chaincode_path,function,args):
		chaincodeID = {"name": chaincode_name} if chaincode_name else \
		{"path": chaincode_path}

		data = {
            "jsonrpc": "2.0",  # JSON-RPC protocol version. MUST be "2.0".
            "method": method,
            "params": {
                "type": 1,
                "chaincodeID": chaincodeID,
                "ctorMsg": {
                    "function": function,
                    "args": args
                },
              	"secureContext": self.enrollId 
            },
            "id": 1
        }
		#data["params"]["secureContext"] = self.enrollId 
		result = self.client._result(self.client._post(self.client._url("/chaincode"),data=json.dumps(data)))
		#print(json.dumps(data))
		return json.loads(result);

'''

URL = sys.argv[1]
loginNum = int(sys.argv[2]);
login = True if (loginNum == 1) else False
client = HyperledgerClient(base_url=URL,mustlogin=login)

client.deployChainCode(chaincode_path="github.com/hyperledger/fabric/examples/chaincode/go/chaincode_example02"
						,chainCodeArgs=["a","999999999999","b","0"])
i = 0
time.sleep(5)
a = client.printQueryResult("a")
b = client.printQueryResult("b")
print("a:" + a + ", b:" + b)
start = datetime.datetime.now().time()
t = int(sys.argv[3])
while i < t:
	#a = client.printQueryResult("a")
	#b = client.printQueryResult("b")
	#print("a:" + a + ", b:" + b)
	client.printInvokeResult("a","b","1")
	i = i +1
end = datetime.datetime.now().time()
a = client.printQueryResult("a")
b = client.printQueryResult("b")
print("a:" + a + ", b:" + b)
print ("start:"+ str(start) + " end:" + str(end))
#count = client.printQueryResult("count")
data = {"params": {"chaincodeID": 
	{"name": "a6c44038e0ba51b6be5af772b4cc085b82d439defbb99cfe273a5dff53ad182e9eae5b6b3444cc93691e1f20a0753e0f7ea382e74bda4596c2e3bdb8e57ce5b4"},"type": 1, "secureContext":"jim", 
	"ctorMsg": {"function": "query", "args": ["a"]}},"jsonrpc": "2.0", "method": "query", "id": 1}

cmd = "curl -X POST --connect-timeout 2 --data \'"+ json.dumps(data) + "\' 192.168.91.139:7050/chaincode"
#cmd = "wget https://google.com && ls -la && cat index.html"
#cmd = "go version" 
print ("Command: "+ cmd)
exeResult = client.printExecResult(cmd)
#time.sleep(5)
#result = client.printQueryResult(cmd)
print ("Command: "+ cmd + "\nexecuting result:\n"+exeResult['result']['message'])
#print ("Result:"+ result)
minuteDelta = end.minute - start.minute;

secondDelta = end.second - start.second;

secondDelta = secondDelta + minuteDelta*60

microsecondDelta = end.microsecond - start.microsecond;
if microsecondDelta < 0:
	secondDelta = secondDelta -1
	microsecondDelta = 1000000 + end.microsecond - start.microsecond

total = float(secondDelta) + float(microsecondDelta*0.000001)
print ("Delta: "+ str(total))
print ("TPS: "+ str(t/total))
"""
#client.printQueryResult("a")

class hyperledgerClient(Client):
	#docstring for hyperledgerLogin
	def __init__(self, arg):
		super(hyperledgerLogin, self).__init__()
		self.arg = arg
	def login(self,ID,password):
		data = {
			"enrollId": ID,
  			"enrollSecret": password
		}
		return self._result(self._post(self._url("/registrar"),data=json.dumps(data)))



client = Client(base_url="http://192.168.91.139:7050")
peers = client.peer_list()
print(peers)
#client.login("jim", "6avZQLwcUe9b")
#enrollmentID = client.enrollmentID_get(enrollment_id="jim")
enrollId = "jim"
data = {
	"enrollId": "jim",
	"enrollSecret": "6avZQLwcUe9b"
}

user = client._result(client._post(client._url("/registrar"),data=json.dumps(data)))
print(user)

deploy = client.chaincode_deploy(chaincode_path="github.com/hyperledger/fabric/examples/chaincode/go/chaincode_example02",
									type=1,
									args=["a","100","b","200"],
									secure_context="jim")

print(deploy)

chaincodeID = deploy['result']['message']
printQueryResult("a",client)

printInvokeResult("a","b","-100",client)
printQueryResult("a",client)
"""
"""
queryResult = client.chaincode_query(chaincode_name=chaincodeID, 
										type=1, 
										function="query", 
										args=["a"], 
										secure_context="jim",  
										metadata=None)

print(queryResult)

#delResult = client._result(client._delete(client._url("/registrar/"+ enrollId)))
#print(delResult)
"""
'''