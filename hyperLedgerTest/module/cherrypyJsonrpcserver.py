import cherrypy
from pyjsonrpc.cp import CherryPyJsonRpc, rpcmethod
import pyjsonrpc
from pymongo import MongoClient
import hashlib,binascii
import random
from datetime import datetime, timedelta
from module import hyperledgerClient
'''
DB_HOST = "192.168.91.139"
DB_NAME = "UsrStatus"
accountCollectionName = "Account"
loginStatusColl = "loginStatus"
ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
hyerLedgerURL="http://192.168.91.139:7050"
Client = hyperledgerClient.HyperledgerClient
HyperLedgerClient = Client(base_url=hyerLedgerURL, mustlogin=True)
DB = MongoClient(host=DB_HOST, port=27017).get_database(name=DB_NAME)
'''
class cherrypy_jsonrpcserver(pyjsonrpc.HttpRequestHandler):
   
    @pyjsonrpc.rpcmethod
    def submit(self, account, password):
       # if args.count < 2:
        #    return  False,"login args error"

        chars = []
        salt = self.randomToken(length=16)
        coll = DB.get_collection(name = accountCollectionName)
        acc = {
            "account" : account
        }
        usr = {
            "account" : account
            , "salt" : salt
            , "password": binascii.hexlify(hashlib.pbkdf2_hmac('sha256', str(password), str(salt), 100000))
        }
        if coll.find(acc).count() >= 1:
            DB.client.close()
            return False, "This account is Already exist"
        coll.insert_one(usr)
        return True,"Submit Success"
    
    @pyjsonrpc.rpcmethod
    def login(self, account, password):
       # if args.count < 2:
       #     return  False, "login args error"
       # account = args[0]
       # password = args[1]
        #DB = MongoClient(host=DB_HOST, port=27017).get_database(name=DB_NAME)
        coll = DB.get_collection(name = accountCollectionName)
        acc = {
            "account" : account
        }
        target = coll.find(acc)
        if target.count() < 1:
            return  False, "This account is not exist"
    
        result = hashlib.pbkdf2_hmac('sha256', password, target[0]['salt'], 100000)
        if  str(binascii.hexlify(result)) == target[0]['password']:
            token = self.randomToken(length=128)
            now = datetime.utcnow()
            time = now + timedelta(hours=1)
            logStColl = DB.get_collection(loginStatusColl)
            logStColl.update_many({"account":account},{"$set":{"enable" : False}})
            #set old login record to invalid
            loginUsr = {
                "account" : account,
                "Token": token,
                "loginDate" :now,
                "timeoutDate" :  time,
                "enable" : True
            }
            loginColl = DB.get_collection(name = loginStatusColl)
            loginColl.insert(loginUsr)
            return True,"Login Success", token, str(time)
        return  False,"Login password error"
    
    @pyjsonrpc.rpcmethod
    def transation(self, account, token, transationNumber, params):
      #  if args.count < 4:
       #     return False, "Args number Error.."
        resultArray = []

        
        try:
            #account = args[0]
            #token = args[1]
            check = self.certificateLoginToken(account, token)
            if not check:
                return False, "certificate error"
        except:
            return False, "Unexpected error"
           
        #transationNumber = int(args[2])
        
        #certParamsNumber = 3
        #for i in range(certParamsNumber,transationNumber+certParamsNumber):
        #    param = args[i]
        result, response = self.execTransation(params['method'], params)
        #resultArray.append({"result":result, "message": response})
        return True, {"result":result, "message": response}
    
    def execTransation(self, function=None, param={}):
    
        if function is None:
            return False, "Error"
        if function == "deploy" :
            try:
                result = HyperLedgerClient.deployChainCode(param['ChaincodePath'], param['chainCodeArgs'])
                return True, result
            except:
                return False, "Unexpected error"
        if not (param.has_key('ChainCodeID')):
            return False ,"Error: ChainCodeID not Found"
        ChainCodeID = param['ChainCodeID']
        if function == "invoke":
            try:
                result = HyperLedgerClient.printInvokeResult(ChainCodeID, param['function'], param['chainCodeArgs'])
            except:
                return False, "Unexpected error"
        if function == "query":
            try:
                result = HyperLedgerClient.printQueryResult(ChainCodeID, param['function'], param['chainCodeArgs'])
            except:
                return False, "Unexpected error"

        return True, result
    '''
@Request.application
def application(request):
    # Dispatcher is dictionary {<method_name>: callable}
    #dispatcher["echo"] = lambda s: s
   # dispatcher["add"] = lambda a, b: str(hash(a+b))
   
    dispatcher.add_method(login, name="login")
    dispatcher.add_method(submit, name="submit")
    dispatcher.add_method(transation, name="transation")
    
    response = JSONRPCResponseManager.handle(
        request.data, dispatcher)
  
    return Response(response.json, mimetype='application/json')
    '''

    def certificateLoginToken(self, account=None, token=None):
        if (account is None) or (token is None):
            return False
        status = {
            #"account": account,
            "Token": token,
            "enable": True
        }
        #DB = MongoClient(host=DB_HOST, port=27017).get_database(name=DB_NAME)
        loginColl = DB.get_collection(name = loginStatusColl)
        result = loginColl.find(status)
        if result.count <= 0 :
            return False
        now = datetime.utcnow()
        for log in result:
            timeout = log['timeoutDate']
            #login record only valid before 'timeout' date,
            #and it must be enable
            if now < timeout:
                return True
        return False
    def randomToken(self, length=16):
        chars = []
        for i in range(length):
            chars.append(random.choice(ALPHABET))
        token = "".join(chars)
        return token


#if __name__ == '__main__':
    #cherrypy.quickstart(cherrypy_jsonrpcserver())
    #run_simple(hostname='localhost', port=4000,application=application, threaded=True)
    '''
    server = jsonrpc.Server(jsonrpc.JsonRpc20(), jsonrpc.TransportTcpIp(addr=("127.0.0.1", 4000), logfunc=jsonrpc.log_file("myrpc.log")))
    server.register_function("login")
    server.register_function("submit")
    server.register_function("transation")
    server.serve()
    '''
    """description of class"""


