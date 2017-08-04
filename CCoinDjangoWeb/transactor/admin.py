from django.contrib import admin
from transactor.Account import Account
from transactor.UserTransactionListFilter import IsValidfilterSpec
from transactor.JsonRPCServerInfo import JsonRPCServerInfo
from transactor.form import JsonRPCServerInfoForm,AccountoForm
from transactor.Transaction import transaction
from django.contrib.admin.filters import  BooleanFieldListFilter
# Register your models here.
class UserAdmin(admin.ModelAdmin):
        list_display = ('email', 'Coins', 'is_Login' )
        form =AccountoForm
        list_filter = (IsValidfilterSpec,)
        pass

class JsonRPCServerInfoAdmin(admin.ModelAdmin):
        list_display = ('name', 'address', 'port', 'enable', 'priority')
        form = JsonRPCServerInfoForm
        pass

admin.site.register(Account, UserAdmin)
admin.site.register(JsonRPCServerInfo, JsonRPCServerInfoAdmin)
admin.site.register(transaction)

