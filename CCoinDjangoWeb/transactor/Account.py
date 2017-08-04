from django.db import models
from transactor.LoginAction import queryTransationList, queryBalance, submitAccount, assginAccount, serverStatusCheck

class AccountManager(models.Manager):
    def createAccount(self, name, password, Coins, isValid):
        account = self.create(email=name, password=password, Coins=Coins)
        print(account)
        return account;
# Create your models here.
class Account(models.Model):
        email =  models.CharField(max_length=120, primary_key=True)
        password =  models.CharField(max_length=120)
        isValid = models.NullBooleanField()
        objects = AccountManager()
        is_Login = models.NullBooleanField(editable=False)
        Coins = models.IntegerField()
        is_submited = models.NullBooleanField(editable=False) 

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            try:
                if self.isValid:
                    self.Coins = queryBalance(self.email)
            except:
                try:
                    self.Coins = -1
                    self.isValid = False
                    self.save()
                except:
                    print("Error from queryBalance!!")
        def save(self, force_insert = False, force_update = False, using = None, update_fields = None):
            if self.isValid and (self.is_submited == None or self.is_submited == False):
                #DO submit
                self.Coins = 1000
                self.is_submited = True
                submitAccount(self.email, self.password)
            elif self.isValid:
                check, result, message = serverStatusCheck()
                if check:
                    result, message  = assginAccount( self.email, str(self.Coins))
                    if not result:
                        return;
            #print("Save account:"+ str(self) )
            return super().save(force_insert, force_update, using, update_fields)
        def __str__(self):
            return self.email
