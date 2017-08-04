from django import forms
from transactor.JsonRPCServerInfo import JsonRPCServerInfo
from transactor.Account import Account
from transactor.LoginAction import  queryBalance
class JsonRPCServerInfoForm(forms.ModelForm):
    class Meta:
        model = JsonRPCServerInfo
        fields = ['name', 'address', 'port', 'enable', 'controlAdminAccount', 'controlAdminPassword', 'priority']
        widgets = {
            'controlAdminPassword': forms.PasswordInput(),
        }
class AccountoForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(AccountoForm, self).__init__(*args, **kwargs)
        instance = getattr(self, 'instance', None)
        self.fields['Coins'].widget.attrs['disabled'] = True
        self.fields['Coins'].required = False
        if instance and instance.pk:
            if not kwargs.get('initial'):
                kwargs['initial'] = {}
            self.fields['password'].widget.attrs['disabled'] = True
            self.fields['password'].required = False
            self.fields['Coins'].widget.attrs['disabled'] = False
            self.fields['Coins'].required = True
           
            #self.Coins.initial =  str(queryBalance(str(instance.email)))
            #kwargs['initial'].update({'Coins': str(queryBalance(str(instance.email)))})
    class Meta:
        model = Account
        fields = ['email', 'password', 'isValid', 'Coins']
        widgets = {
            'password': forms.PasswordInput(attrs={'required': False}),
        }