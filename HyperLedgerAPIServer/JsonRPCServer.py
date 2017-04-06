#-*-coding:utf-8 -*-
from werkzeug.wrappers import Request, Response
from werkzeug.serving import run_simple
from jsonrpc import JSONRPCResponseManager, dispatcher 
from pymongo import MongoClient
import pymongo
import hashlib,binascii
import random
from datetime import datetime, timedelta
from module import hyperledgerClient
import cherrypy
import json
import sys
@dispatcher.add_method
def submit(*args, **kwargs):
    if args.count < 2:
        return  False,"login args error"
    account = args[0]
    password = args[1]
    chars = []
    salt = randomToken(length=16)
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
        #DB.client.close()
        return False, "This account is Already exist."
    coll.insert_one(usr)
    submit = {
            'method': 'invoke',
            'ChainCodeID' : DeployChaincodeID,
            'function':"createAccount",
            'chainCodeArgs':[account,"100000000000000000"]
        }
    try:
        print DeployChaincodeID
        execResult, message = execTransation(Method="invoke", param=submit, executeUser=MasterAdmin)
    except:
        coll.delete_many(usr)
        return False, "Create Account failure..."
    if not execResult:
        coll.delete_many(usr)
        return execResult, Message
    try:
       return True, message['result']['message']
    except:
       coll.delete_many(usr)
       return False, message['error']['message']
@dispatcher.add_method
def login(*args, **kwargs):
    if args.count < 2:
        return  False, "login args error"
    account = args[0]
    password = args[1]
    #DB = MongoClient(host=DB_HOST, port=27017).get_database(name=DB_NAME)
    result, message, target = accountCheck(account=account)
    if not result:
        return  False, "This account is not exist."
    result = hashlib.pbkdf2_hmac('sha256', password, target[0]['salt'], 100000)
    if  str(binascii.hexlify(result)) == target[0]['password']:
        token = randomToken(length=128)
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
@dispatcher.add_method
def logout(*args, **kwargs):
    # [MainAccount] [MainAccountCertToken] [TargetAccount] //管理者可以強制登出任何人
    # normal user: MainAccount == TargetAccount, Admin user: MainAccount == 'admin' and TargetAccount == 'OtherUser'
    if args.count < 3:
        return False, "Args number Error.."

    MainAccount = args[0]
    MainAccountCertToken = args[1]
    TargetAccount = args[2]

    if not certificateLoginToken(account=MainAccount,token=MainAccountCertToken):
        return False, "certificate error"
    #Check Target account is exist
    if (not MainAccount == MasterAdmin) and (not MainAccount == TargetAccount):
        return False, "Normal user can not logout other user."
    check, Message, target = accountCheck(TargetAccount)
    if not check:
        print Message
        return False, "Target account is not exist."
    try:
        logStColl = DB.get_collection(loginStatusColl)
        logStColl.update_many({"account":TargetAccount},{"$set":{"enable" : False}})
    except:
        return False, "Logout failure"

    return True, "Logout Success"
    
@dispatcher.add_method
def transfer(*args, **kwargs):
    # [MainAccount] [MainAccountCertToken] [TargetAccount] [Coins] 
    if args.count < 4:
        return False, "Args number Error.."
    try:
        MainAccount = args[0]
        MainAccountCertToken = args[1]
        TargetAccount = args[2]
        Coins = int(args[3])
    except:
        return False, "args format Error:" + str(args)
    if not certificateLoginToken(account=MainAccount,token=MainAccountCertToken):
        return False, "certificate error"
    #Check Target account is exist
    check, Message,_ = accountCheck(TargetAccount)
    if not check:
        print Message
        return False, "Target account is not exist."
    transferParam = {
        'method': 'invoke',
        "function":"transfer",
        "chainCodeArgs":[MainAccount,TargetAccount,str(Coins)],
        "ChainCodeID":DeployChaincodeID
        }
    
    try:
        execResult, message = execTransation(Method="invoke", param=transferParam, executeUser=MasterAdmin)
    except: 
        return False, "Unexpected error: "+ message['error']['message']
    if not execResult:
        return execResult, "Execute failure: "+ message
    try:
       return True, "Start transfer Coins!"
    except:
       return False, message['error']['message']
@dispatcher.add_method
def queryBalance(*args, **kwargs):
    # [account] [accountToken] [targetAccount]// 僅有使用者自己與管理者可以查詢，該使用者的帳本
    # normal user: account == targetAccount, Admin user: account == 'admin' and targetAccount == 'OtherUser'
    try:
       result, message = queryUserLedger(*args)
       if not result:
            return False, message
      #print json.loads(coin)['Coin']
       return True, message['Coin']
    except:
       return False, message
@dispatcher.add_method
def queryTransationList(*args, **kwargs):
    # [account] [accountToken] [targetAccount]// 僅有使用者自己與管理者可以查詢，該使用者的帳本
    # normal user: account == targetAccount, Admin user: account == 'admin' and targetAccount == 'OtherUser'

    try:
       result, message = queryUserLedger(*args)
       if not result:
            return False, message
      #print json.loads(coin)['Coin']
       return True, message['Transations']
    except:
       return False, message

@dispatcher.add_method
def transation(*args, **kwargs):
    if args.count < 4:
        return False, "Args number Error.."
    resultArray = []
    try:
        account = args[0]
        token = args[1]
        check = certificateLoginToken(account, token)
        if not check:
            return False, "certificate error"
    except:
        return False, "Unexpected error in certificate stage"
    transationNumber = int(args[2])
    certParamsNumber = 3
    for i in range(certParamsNumber,transationNumber+certParamsNumber):
        param = args[i]
        result, response = execTransation(param['method'],param,args[0])
        resultArray.append({"result":result, "message": response})
    return True, resultArray
def execTransation(Method=None, param={}, executeUser=None):
    if not executeUser == MasterAdmin:
        return False, "Only admin can execution transation."
    if Method is None or executeUser is None:
        return False, "Error"
    if Method == "deploy" :
        try:
            result = HyperLedgerClient.deployChainCode(param['ChaincodePath'], param['chainCodeArgs'])
            return True, result
        except:
            return False, "Unexpected error in deploy stage"
    if not (param.has_key('ChainCodeID')):
        return False ,"Error: ChainCodeID not Found"
    ChainCodeID = param['ChainCodeID']
    if Method == "invoke":
        try:
            result = HyperLedgerClient.printInvokeResult(ChainCodeID, param['function'], param['chainCodeArgs'])
        except:
            return False, "Unexpected error in invoke stage"
    if Method == "query":
        try:
            if executeUser == param['chainCodeArgs'][0] or executeUser == MasterAdmin:
                result = HyperLedgerClient.printQueryResult(ChainCodeID, param['function'], param['chainCodeArgs'])
            else:
                return False, "Can not Query other User!"
        except:
            return False, "Unexpected error in query stage"

    return True, result
@Request.application
def application(request):
    dispatcher.add_method(login, name="login")
    dispatcher.add_method(submit, name="submit")
    dispatcher.add_method(transation, name="transation")
    dispatcher.add_method(transfer, name="transfer")
    dispatcher.add_method(queryBalance, name="queryBalance")

    response = JSONRPCResponseManager.handle(
        request.data, dispatcher)
  
    return Response(response.json, mimetype='application/json')
def queryUserLedger(*args):
    # [account] [accountToken] [targetAccount]// 僅有使用者自己與管理者可以查詢，該使用者的帳本
    # normal user: account == targetAccount, Admin user: account == 'admin' and targetAccount == 'OtherUser'
    if len(args) != 3:
        return False, "Args number Error"
    #print "Start Query!"
    try:
        account = args[0]
        token = args[1]
        check = certificateLoginToken(account, token)
        targetAccount = args[2]
        if not check:
            return False, "Certificate error"
        query = {
            'method': 'invoke',
            "function":"query",
            "chainCodeArgs":[targetAccount],
            "ChainCodeID": DeployChaincodeID
        }
    except:
        return False, "Unexpected error in certificate stage"
    check, message, target = accountCheck(targetAccount)
    if not check:
        return False, "Query: Account is not exist." # admin query
    if (not account == MasterAdmin) and (not account == targetAccount):
        return False, "Normal user can not query other user."
    #print "Going to blockchain Query!"
    try:
        execResult, message = execTransation(Method="query",param=query, executeUser=MasterAdmin)
    except:
        return False, "Query \'" +targetAccount+ "\' error!"
    if not execResult:
        return execResult, "Query failure: "+ message
    try:
       coin = message['result']['message']
      #print json.loads(coin)['Coin']
       return True, json.loads(coin)
    except:
       return False, message['error']['message']

def certificateLoginToken(account=None, token=None):
    if (account is None) or (token is None):
        return False
    status = {
        "account": account,
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
def accountCheck(account=None):
    accountJSON = {
         "account":account,
        }
    accountColl = DB.get_collection(name = accountCollectionName)
    result = accountColl.find(accountJSON)
    if result.count() != 1:
        return False, "Error: Account is Not exist or Unexpected Account submit Error", result
    return True, "Ok! This account is exist." ,result

def randomToken(length=16):
    chars = []
    for i in range(length):
        chars.append(random.choice(ALPHABET))
    token = "".join(chars)
    return token
def startSetting():

    rootToken=randomToken(256)
    adminCheck ={
        "account":MasterAdmin
    }

    admin={
        "account":MasterAdmin,
        "salt":rootToken,
        "password":binascii.hexlify(hashlib.pbkdf2_hmac('sha256', str("admin"), str(rootToken), 100000))
        # Default admin password.
    }
    loginCol = DB.get_collection(name=loginStatusColl)
    try:
        loginCol.ensure_index("timeoutDate", expireAfterSeconds=0)
    except:
        print "Already auto delete timeout Configure"
    adminColl = DB.get_collection(name = accountCollectionName)
    result = adminColl.find(adminCheck)
    if result.count() < 1:
        adminColl.insert_one(admin)
    #Create default admin account 

    deploy = {
        'ChaincodePath': deployChaincodePath,
        'chainCodeArgs': ["N/A"]
        }
    deployChaincode, resultMessage = execTransation(Method="deploy", param=deploy, executeUser=MasterAdmin)
    if not deployChaincode:
        return False, "Init Deploy Failure:" + resultMessage
    else:
        try:
            DeployChaincodeID = resultMessage['result']['message']
        except:
             return False, "Get deploy Chaincode ID Error"
    return True, "OK! Init is finished! \nDeploy Chaincode ID is \'" + DeployChaincodeID + "\'", DeployChaincodeID

if __name__ == '__main__':
    if len(sys.argv) != 3:
        DB_IP = "192.168.91.139"
        BC_IP = "http://192.168.91.139:7050"
    else:
        DB_IP = sys.argv[1]
        BC_IP = sys.argv[2]
    #DB config 
    MasterAdmin = "admin"
    DB_HOST = DB_IP
    DB_NAME = "UsrStatus"
    #DB table: Account -> main account loginStatus -> login record
    accountCollectionName = "Account"
    loginStatusColl = "loginStatus"
    #random params
    ALPHABET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
    #hyperledger fabric ver 0.6 param
    hyerLedgerURL=BC_IP
    Client = hyperledgerClient.HyperledgerClient
    HyperLedgerClient = Client(base_url=hyerLedgerURL, mustlogin=True)
    deployChaincodePath ="github.com/hyperledger/fabric/myChaincode"
    DB = MongoClient(host=DB_HOST, port=27017).get_database(name=DB_NAME)
    result, Message, chaincodeID = startSetting()
    print Message
    if result:
        DeployChaincodeID = chaincodeID
        run_simple(hostname='0.0.0.0', port=4000, application=application, threaded=True, ssl_context=None)
    else:
        print "Error -> exit"
