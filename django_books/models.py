
from uuid import uuid4
from datetime import datetime 
from django.db import models


class ServiceAccount(models.Model): 
    name = models.CharField(max_length=30)
    qbid = models.UUIDField(default=uuid4)
    created_on = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    password = models.CharField(max_length=30, default='test')

    def __str__(self): 
        return self.name

class TicketQueue(models.Model):
    STATUS = (
        ('1', 'Created', ),
        ('5', 'Approved'),
        ('2', 'Running', ),
        ('6', 'Error'),
        ('3', 'Failed', ),
        ('4', 'Success'),
    )
    status = models.CharField(max_length=15, choices=STATUS)
    ticket = models.UUIDField(default=uuid4)
    # Batch method that bundles similar objects together and assisgns the same 
    # Ticket if to be processed at once... 
    # 20 expenses are ready to be approved: 
    #   - select expenses approve
    #   - tickets go from pending to approved  
    #   - ticket is created 
    #   - Many to one relationship?
    #   - All expenses are updated to use the same ticket number for processings 
    #   - Ticket does reverse lookup to get a list of all objects that use it as 
    # a foreign key - iterates through all objects until completion 
    #   - Each objects is updated on processing - Success, error, fail... 
    object_type = models.CharField(max_length = 20, blank=True, null=True)
    approved_date = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)