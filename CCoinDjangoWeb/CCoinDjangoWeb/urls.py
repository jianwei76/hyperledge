"""
Definition of urls for CCoinDjangoWeb.
"""

from django.conf.urls import include, url
from django.contrib import admin
from transactor.views import loginView, submitView, submit
from transactor.LoginAction import login, logout, postTransaction

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = [
    # Examples:
    # url(r'^$', CCoinDjangoWeb.views.home, name='home'),
    # url(r'^CCoinDjangoWeb/', include('CCoinDjangoWeb.CCoinDjangoWeb.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
    url(r'^$',  include('transactor.urls')),
    #url(r'^transactor/', include('transactor.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^login/$', loginView),
    url(r'^submit/$', submitView),
    url(r'^login/action$', login, name='login'),
    url(r'^submit/action$', submit , name='submit'),
    url(r'^logout/action$', logout, name='logout'),
    url(r'^transaction/action$', postTransaction, name='transaction'),
]
admin.site.site_header = 'CCoin Web Administration'