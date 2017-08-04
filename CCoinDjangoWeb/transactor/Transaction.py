from django.db import models

# Create your models here.
class transaction(models.Model):
        NORMAL_TANSFER=0
        ADMIN_TANSFER=1
        ADMIN_ASSGIN=2
        TYPE_CHOICES = (
            (NORMAL_TANSFER, 'Normal Transfer'),
            (ADMIN_TANSFER, 'Admin Transfer'),
            (ADMIN_ASSGIN, 'Admin Assgin'),
        )
        owner = models.CharField(max_length=128, default="test")    
        id =  models.CharField(max_length=512, primary_key=True)
        toUser =  models.CharField(max_length=120)
        coins = models.CharField(max_length=120)
        date = models.CharField(max_length=120)
        objects = models.Manager
        type = models.IntegerField(choices=TYPE_CHOICES)
      
        @property
        def getTypeString(self):
            return self.TYPE_CHOICES[self.type][1]
        def __str__(self):
           
            return self.id
