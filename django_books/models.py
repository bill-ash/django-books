
from datetime import datetime 
from uuid import uuid4

from django.db import models

# model name must be lowercase and unique 
from django.contrib.contenttypes.models import ContentType 

from django.contrib.auth import get_user_model

class ServiceAccount(models.Model): 
    
    # Name of the QuickBooks File 
    name = models.CharField(max_length=30)

    # The file path for the QB file 
    file_path = models.CharField(max_length=90, blank=True, null=True)
    app_url = models.CharField(max_length=90, blank=True, null=True)
    
    # UUID to use in the .qwc file 
    qbid = models.CharField(max_length=50, default=uuid4)
    created_on = models.DateTimeField(auto_now_add=True)
    last_updated = models.DateTimeField(auto_now=True)
    
    # Default password - \\TODO hash this
    password = models.CharField(max_length=30, default='test')

    is_active = models.BooleanField(default=True)

    config = models.TextField(null=True, blank=True)

    @staticmethod
    def create_qwc_file(app_name='Django Books', url='http://localhost:8080', username=uuid4(), sync_time=0): 
        return f"""
            <?xml version='1.0' encoding='UTF-8'?>
            <QBWCXML>
                <AppName>{app_name}</AppName>
                <AppID></AppID>
                <AppURL>{url}/webconnector/</AppURL>
                <AppDescription>Django QuickBooks WebConnector</AppDescription>
                <AppSupport>{url}/support/</AppSupport>
                <UserName>{username}</UserName>
                <OwnerID>{{{uuid4()}}}</OwnerID>
                <FileID>{{{uuid4()}}}</FileID>
                <QBType>QBFS</QBType>
                <Scheduler><RunEveryNMinutes>{sync_time}</RunEveryNMinutes></Scheduler>
            </QBWCXML>
        """

    def save(self, *args, **kwargs):
        self.config = self.create_qwc_file(app_name=self.name, url=self.app_url, username=self.qbid, sync_time=0)
        super(ServiceAccount, self).save(*args, **kwargs)

        
    def __str__(self): 
        return self.name
     

class TicketManager(models.Manager): 
    
    def get_tickets(self):
        """
        Used during authentication - determines whether or not there is new work 
        to process
        """ 
        return self.filter(status=TicketQueue.TicketStatus.CREATED).count()
    
    def get_next_ticket(self):
        return self.filter(status=TicketQueue.TicketStatus.CREATED).first().ticket

    def post_next_query(self):
        """
        When working with a ticket that has many transaction associated with it, returns 
        the next iteration. 
        """
        pass 


class TicketQueue(models.Model):
    class TicketStatus(models.TextChoices):
        """
        Methods that change state in QuickBooks require a status of 2. GET requests, can 
        proceed with 1, or greater. 
         """

        # A ticket has been created for work to be preformed
        CREATED = ('1', 'Created')

        # Tickets that change state in QB require approval    
        APPROVED = ('2', 'Approved')
            
        # Ticket is currently being worked on by QBWC
        PROCESSING = ('3', 'Processing')
        
        # All work was successfully completed 
        SUCCESS = ('4', 'Success')
        
        # There was an error but some work may have been complete 
        ERROR = ('5', 'Error')
        
        # Network connection issue or total failure 
        FAILED  = ('6', 'Failed')

    class TicketMethod(models.TextChoices):
        GET = ('GET', 'GET')
        POST = ('POST', 'POST')
        PATCH = ('PATCH', 'PATCH')
    

    ticket = models.CharField(default=uuid4, max_length=123)
    status = models.CharField(
        max_length=5, 
        choices=TicketStatus.choices,
        default=TicketStatus.CREATED
    )
    method = models.CharField(choices=TicketMethod.choices, max_length=5, default='GET')

    # More research: 
    # https://github.com/CiCiUi/django-db-logger
    # Requirement: log all requests & responses with QB 
    # event_log = models.ForeignKey('TicketLog', )

    # pg limit 
    model = models.CharField(max_length=63) 
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
    # object = models.CharField(max_length = 20, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    # On error - screen for filtering for all error requests 
    # On Error - resolved == False 
    resolved = models.BooleanField(default=True)
    resolved_by = models.ForeignKey(
        get_user_model(), 
        blank=True, 
        null=True,
        on_delete=models.SET_NULL
    )

    # Sets the default model manager 
    objects = models.Manager()
    process = TicketManager()


    def get_model(self): 
        """
        User defines methods in application to be executed by the web connector. 

        Returns:
            Model: models.Model
        """
        ct = ContentType.objects.get(model=self.model.lower()) 
        model = ct.model_class()
        return model 

    def __str__(self): 
        return self.model


class BaseObjectMixin(models.Model): 
    """
    Every object that inherits from BaseObject, get's a batch method that will enable it to 
    insert or update records in QuickBooks. By default, every method is un-batched. When objects
    are approved to change state in QuickBooks, they will get supplied with ticket id that also 
    contains the request method and xml for processing. 
    """

    class BatchStatus(models.TextChoices): 
        BATCHED = ('BATCHED', 'BATCHED')
        UN_BATCHED = ('UN_BATCHED', 'UN_BATCHED')

    _batch_id = models.CharField(
        max_length=124, 
        blank=True, 
        null=True
        )

    _batch_status = models.CharField(
        max_length=30,
        choices=BatchStatus.choices,
        default=BatchStatus.UN_BATCHED
    )

    # QuickBooks Fields
    _list_id = models.CharField(max_length=120, 
        blank=True, 
        null=True
        )
    _time_created = models.DateTimeField(blank=True, null=True)
    _time_modified = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def get_query(*args, **kwargs): 
        raise NotImplementedError
        
    @staticmethod
    def post_query(*args, **kwargs): 
        raise NotImplementedError

    @staticmethod
    def patch_query(*args, **kwargs): 
        raise NotImplementedError

    @staticmethod
    def process_get(*args, **kwargs): 
        raise NotImplementedError

    @staticmethod
    def process_post(*args, **kwargs): 
        raise NotImplementedError

    @staticmethod
    def process_patch(*args, **kwargs): 
        raise NotImplementedError
    
    def batch_model(self, ticket, *args, **kwargs):
        """
        The inheriting model gets a batch_model() method that assigns the ticket number (batch_id)
        to the object. We can now batch all objects that have a ticket id and a 
        """
        self._batch_id = ticket
        self.save()

    class Meta: 
        abstract = True

    
