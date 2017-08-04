# -*- coding: utf-8 -*-
from django.shortcuts import get_object_or_404, render,render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from transactor.Transaction import transaction
from transactor.JsonRPCServerInfo import JsonRPCServerInfo
from django.views.decorators.csrf import requires_csrf_token
import requests
import json
from django.db.models import Q

def serverStatusCheck():
    mode = JsonRPCServerInfo.STATUS_CHOICES[0]
    result = JsonRPCServerInfo.objects.filter(enable=True, priority=mode[0])
    if len(result) < 1:
        return False ,None ,"All server is not enable."
    return True, result[0], "Ok ";
def requestsRPC(payload={}):
    check, result, message = serverStatusCheck()
    if not check:
        return check, message;
    url = "http://"+ result.address + ":" + str(result.port)
    headers = {'content-type': 'application/json'}
    print(url+":" + str(payload))
    response = requests.post(
        url, data=json.dumps(payload), headers=headers).json()
    print(response)
    return True, response
@requires_csrf_token
def login(request):
    if request.method == "POST":
        acc = request.POST['loginAccount']
        passwd = request.POST['loginPassword']
        #account = Account.objects.createAccount(name=acc,password=passwd,isValid=True)
        error=False
        if not str(acc) or not str(passwd):
            error = True
        if error:  
            return render(request,'loginPage.html', {'error':error});
        #do login
        loginPayload = {
            "method": "login",
            "params": [acc, passwd],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, result = requestsRPC(loginPayload)
        if check and result['result'][0]:
            #account = Account.objects.filter(email=acc)[0];
            request.session['login']= str(acc)
            request.session['loginToken']= str(result['result'][2])
            request.session['Balance'] = queryBalance(acc)
            request.session.set_expiry(1500) # 1500/60 = 25
            try:
                _thread.start_new_thread( queryTransationList, (acc, str(result['result'][2]), acc) )
            except:
                print("Error Query Transaction List error..")
            #queryTransationList(acc, str(result['result'][2]), acc)
            return HttpResponseRedirect("/")
        
        error = True
        if error:  
            return render(request,'loginPage.html', {'error':error});

def submitAccount(account, passwd):
        submitPayload = {
            "method": "submit",
            "params": [account, passwd],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, result = requestsRPC(submitPayload)
        return check,result;
def assginAccount(targetAccount, coins):
        check, result, message = serverStatusCheck()
        if not check:
            return check, message;
        adminAccount = result.controlAdminAccount
        adminPassword = result.controlAdminPassword
        loginPayload = {
            "method": "login",
            "params": [adminAccount, adminPassword],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, logIn = requestsRPC(loginPayload)
        loginID = logIn['result'][2]
        assginAccountPayload = {
            "method": "modifyAccount",
            "params": [adminAccount, loginID, targetAccount, coins ],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, result = requestsRPC(assginAccountPayload)
        logoutPayload={
            "method": "logout",
            "params": [adminAccount, loginID , adminAccount],
            "jsonrpc": "2.0",
            "id": 0, 
        }
        requestsRPC(logoutPayload)
        return check, result;
@requires_csrf_token
def logout(request):
        if request.method == "POST":
            account = request.session['login']
            token = request.session['loginToken']
            transaction.objects.filter(owner=account).delete()
            logoutPayload={
                "method": "logout",
                "params": [account, token, account],
                "jsonrpc": "2.0",
                "id": 0,
            }
            if request.session.get('login') != None:
                del request.session['login']
            if request.session.get('loginToken') != None:
                del request.session['loginToken']
            if request.session.get('Balance') != None:
                del request.session['Balance'] 

            check, result = requestsRPC(logoutPayload)    
            return HttpResponseRedirect("/")
def queryBalance(target):
        check, result, message = serverStatusCheck()
        if not check:
            return check, message;
        adminAccount = result.controlAdminAccount
        adminPassword = result.controlAdminPassword
        loginPayload = {
            "method": "login",
            "params": [adminAccount, adminPassword],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, logIn = requestsRPC(loginPayload)
        loginID = logIn['result'][2]
        logoutPayload={
            "method": "logout",
            "params": [adminAccount, loginID , adminAccount],
            "jsonrpc": "2.0",
            "id": 0, 
        }
        queryPayload = {
            "method": "queryBalance",
            "params": [adminAccount, loginID, target],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, result = requestsRPC(queryPayload)
        try:
            if check and result['result'][0]:
                if result['result'][1] == None:
                    requestsRPC(logoutPayload)
                    return None;
                Coins =  result['result'][1]
        except:
            Coins = "-"
        requestsRPC(logoutPayload)
        return Coins
def queryTransationList(account ,token ,target):
        queryPayload = {
            "method": "queryTransationList",
            "params": [account, token, target],
            "jsonrpc": "2.0",
            "id": 0,
        }
        
        check, result = requestsRPC(queryPayload)
        try:
            if check and result['result'][0]:
                if result['result'][1] == None:
                    return None;
                list = result['result'][1]
                transaction.objects.filter(Q(owner=account) | Q(toUser=account)).delete()
                print(str(list[0]))
                for t in list:
                    queryTransactionPayload={
                        "method": "queryTransaction",
                        "params": [account, token , t],
                        "jsonrpc": "2.0",
                        "id": 0, 
                    }
                    check, result = requestsRPC(queryTransactionPayload)
                    tranaction = result['result'][1]
                    if check:
                        toUser = tranaction['Details']['ToID']
                        FromUser = tranaction['Details']['FromID']
                        coin = tranaction['Details']['Coins']
                        ids = tranaction['TransationID']
                        date = tranaction['Details']['Date']      
                        type = tranaction['Details']['TransationType']  
                        tr = transaction(id=ids, toUser=toUser, owner=FromUser, coins=coin, date=date, type=type)
                        tr.save()
                return list
        except:
            print("Error:" + result['error'])
            return None

        return None
@requires_csrf_token
def postTransaction(request):
 
    if request.method == "POST" and request.session.get('login') != None:
        #print(request.POST)
        toUser = request.POST['TrnasactionTargert']
        coins = request.POST['TrnasactionCoin']
        coinsNumber = int(coins)
        if coinsNumber <= 0:
            print("Error: Coins number must great than zero.")
            request.session['transactionPost'] = "Error: Coins number must great than zero."
            return HttpResponseRedirect("/")
        fromUser = request.session.get('login') 
        token = request.session['loginToken']
        if toUser == fromUser : 
            request.session['transactionPost'] = "不可以對自己發起交易"
            return HttpResponseRedirect("/")
        postTransactionPayload={
            "method": "transfer",
            "params": [fromUser, token, toUser, coins],
            "jsonrpc": "2.0",
            "id": 0,
        }
        check, result = requestsRPC(postTransactionPayload)
        try:
            if check and result['result'][0]:
                if result['result'][1] == None:
                    return HttpResponseRedirect("/")

                request.session['transactionPost'] = result['result'][1]
                print(result)
                return HttpResponseRedirect("/")
        except:
            print("Error:" + result['error'])
            request.session['transactionPost'] = result['error']
            return HttpResponseRedirect("/")
    request.session['transactionPost'] = "You must login first."
    return HttpResponseRedirect("/")