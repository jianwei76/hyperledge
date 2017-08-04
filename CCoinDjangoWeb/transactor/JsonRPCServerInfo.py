from django.db import models
from django import forms
class JsonRPCServerInfo(models.Model):
    DEBUG = 0
    PUBLIC = 1
    PRIVATE = 2
    STATUS_CHOICES = (
        (DEBUG, 'Debug'),
        (PUBLIC, 'Public'),
        (PRIVATE, 'Private'),
    )
    priority = models.IntegerField(choices=STATUS_CHOICES)
    name = models.CharField(max_length=120)
    address = models.CharField(max_length=120)
    port = models.IntegerField()
    enable = models.NullBooleanField()
    objects = models.Manager
    controlAdminAccount = models.CharField(max_length=120, default="test")
    controlAdminPassword = models.CharField(max_length=120, default="test") 
    def __str__(self):
        enableStr = "Disable";
        if self.enable:
            enableStr = "Enable"

        return enableStr + " / " + str(self.STATUS_CHOICES[self.priority][1]) +" / "+ self.name + " (" + self.address +":" + str(self.port) + ")" 
        

    """description of class"""


