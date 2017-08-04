from django.shortcuts import render, render_to_response
from django.template.loader import render_to_string
from django.template import loader, Context,RequestContext
from django.http import HttpResponseRedirect, HttpResponse
from django import forms
from transactor.LoginAction import queryTransationList, queryBalance, submitAccount
import json
from django.views.decorators.csrf import requires_csrf_token
from transactor.Transaction import transaction
import datetime
from django.db.models import Q
import _thread
from transactor.Account import Account 
# Create your views here.
@requires_csrf_token
def index(request):
    #t1 = transactionsView(id="1111111111",toUser="11111",coins=10, date="11/111/11")
    #table = 'TransactionListTitle.html';
    table = 'TransactionListTitleTable.html'
    template = render_to_string(table,{'TableTransactionControlID':"testt123"})
    mustRefresh = False
    isAdmin = False
    if request.session.get('lastAccessTime') == None:
        request.session['lastAccessTime'] = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
    else :
        date = datetime.datetime.strptime(request.session.get('lastAccessTime'),'%Y-%m-%d %H:%M:%S.%f')
        nowDate = datetime.datetime.now()
        diff = nowDate - date
        print("time:" + str(diff));
        if diff.total_seconds() > 30:
            print("Timeout!! - " + str(diff));
            mustRefresh =True
            request.session['lastAccessTime'] = str(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f'))
    error = False
    isLogin=False
    loginMessage = ""
    transactionPostResult = ""
    transactionPost = False
    Coins = "-"

    if request.session.get('login') != None:
        if request.session.get('login') != None:
            account = str(request.session.get('login'))
        if request.session.get('loginToken') != None:
            token = str(request.session.get('loginToken'))
        if request.session.get('Balance') != None:
            Coins = str(request.session.get('Balance')) 
        #print('Login success:' + str(request.session.get('login')))
        #print('Login success:' + str(request.session))
        if mustRefresh:
            try:
                _thread.start_new_thread( queryTransationList, (account ,token ,account) )
            except:
                print("Error Query Transaction List error..")
            request.session['Balance'] = str(queryBalance(account))
            Coins = str(request.session.get('Balance')) 
            mustRefresh =False
        isLogin=True
        loginMessage = account
        transactionLists = transaction.objects.filter(Q(owner=account) | Q(toUser=account))
        print(str(transactionLists))
        template = render_to_string(table,{'isLogin': isLogin, 'TableTransactionControlID':"list", 'TransactionLists':transactionLists})

    if request.session.get('transactionPost') != None:
        transactionPostResult = request.session.get('transactionPost')
        transactionPost = True
        del request.session['transactionPost']
    else :
        transactionPost = False  
    return render(request, 'index.html', {
        'Title':"C-Coin",
        'StatusTitle':"C-Coin Status",
        'firstStatus':"RPC Server",
        'SecStatus':"MongoDB",
        'thirdStatus':"BLockChain",
        'fourStatus':"Total",
        'TransactionTitle':"Publish a transaction",
        'TransactionListTitle':"Transaction List",
        'LOGIN_STATUS':"LOGIN",
        'LOGOUT_STATUS':"LOGOUT",
        'JSONRPCServer':" Connected to C-Coin System: 140.92.13.145",
        'Configure':"Configure",
        'isLogin':isLogin,
        'loginMessage':loginMessage,
        'transactionList':template,
        'transactionPostResult':transactionPostResult,
        'transactionPost':transactionPost,
        'UserCoins':Coins,
        'isAdmin':isAdmin
    })

def loginView(request):
        error=False
        return render(request, 'loginPage.html')

def submitView(request):
        error=False
        return render(request, 'submitPage.html')

@requires_csrf_token
def submit(request):
    if request.method == "POST":
        print(request.POST)
        acc = request.POST['submitAccount']
        passwd = request.POST['submitPassword']
        repasswd = request.POST['submitRePassword']
        #account = Account.objects.createAccount(name=acc,password=passwd,isValid=True)
        error=False
        if not str(acc) or not str(passwd) or not str(repasswd):
            error = True
        elif passwd != repasswd:
            error = True
        if error:  
            message = "Error: " + "密碼輸入不一致"
            return render(request,'submitPage.html', {'error':error, 'ErrorMessage': message});

        check, result = submitAccount(acc, passwd)
        accountObject = Account(email=acc, password=passwd, isValid=True, is_submited=True, Coins="1000")
        accountObject.save()
        print(result)
        error = not check
        try:
            if error or (not result['result'][0]):  
                error = True
                message = "Error: " + str(result['result'][1])
                return render(request,'submitPage.html', {'error':error, 'ErrorMessage': message});
        except:
            message = "Error: " + str(result)
            error = True
            print(message)
            return render(request,'submitPage.html', {'error':error, 'ErrorMessage': message});
        return HttpResponseRedirect("/")