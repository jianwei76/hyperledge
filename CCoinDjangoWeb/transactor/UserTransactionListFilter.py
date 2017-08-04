from django.contrib import admin
from django.utils.translation import ugettext_lazy as _
class IsValidfilterSpec(admin.SimpleListFilter):
    title = _('Is Valid')
    parameter_name = 'Valid'         
    def lookups(self, request, model_admin):
        return (
          ('DEBUG', _('DEBUG')),
        )
    
    def queryset(self, request, queryset):
        if self.value() == 'DEBUG':
             return queryset.all()
        return queryset.filter(isValid=True)
