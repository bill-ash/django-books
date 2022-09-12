
from datetime import datetime 
from uuid import uuid4

from django.db import models

# model name must be lowercase and unique 
from django.contrib.contenttypes.models import ContentType 

from django.contrib.auth import get_user_model

class ServiceAccount(models.Model): 
    """
    Service account for the associated QuickBooks file. Generates a .qwc config to be 
    installed to the QuickBooks web connector. The name, corresponds to the name of the 
    application or integration goal. File path provides the option to ensure we're updating 
    or querying the correct QuickBooks file. If a file moves, or is re-named, this would prevent
    the calling application from making any changes. 
    
    URL is the url of the calling app. Must be https:// or localhost. 

    qbid is the guid of the user the web connector will try to auth before accepting new tickets. 

    Password as plain text is helpful for development. No serious risk of exposing even in a security incident 
    since queries can only be made from QuickBooks and after the UUID is checked as user. 
    """
    
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
    def create_qwc_file(app_name='Django Books', url='http://localhost:8080', username=uuid4(), sync_time=60): 
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
                <Scheduler>
                    <RunEveryNMinutes>{sync_time}</RunEveryNMinutes>
                </Scheduler>
            </QBWCXML>
        """

    def save(self, *args, **kwargs):
        self.config = self.create_qwc_file(app_name=self.name, url=self.app_url, username=self.qbid)
        super(ServiceAccount, self).save(*args, **kwargs)

    def __str__(self): 
        return self.name
     

class TicketManager(models.Manager): 
    "Used for managing work to be preformed by the web connector."
    
    def count_queue(self):
        "Called during authentication; determines whether new work is available."
        return self.filter(status=TicketQueue.TicketStatus.CREATED).count()

    def get_next_ticket(self):
        "Called during authentication; returns the next ticket in the stack."
        return self.filter(status=TicketQueue.TicketStatus.CREATED).first().ticket


class TicketQueue(models.Model):
    class TicketStatus(models.TextChoices):
        "Inserts and updates must be APPROVED before being sent."

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
    method = models.CharField(
        choices=TicketMethod.choices,
        max_length=5,
        default=TicketMethod.GET
    )

    # More research: 
    # https://github.com/CiCiUi/django-db-logger
    # Requirement: log all requests & responses with QB 
    message_log = models.TextField(blank=True,null=True)

    # pg column character limit 
    model = models.CharField(max_length=63) 
   
    created_at = models.DateTimeField(auto_now_add=True)
    last_update = models.DateTimeField(auto_now=True)

    
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

    def get_logs(self, *args, **kwargs):
        
        message_log = self.logs.all()
        
        if message_log:
            self.message_log = '\n'.join([c.message for c in message_log])
        else: 
            self.message_log = ''

    def save(self, *args, **kwargs): 
        self.get_logs()
        super(TicketQueue, self).save(*args, **kwargs)

    def __str__(self): 
        return self.model


class BaseObjectManager(models.Manager): 
    
    def check_for_work(self, ticket, *args, **kwargs): 
        """
        Checks the calling model for status unbatched with current ticket id. Ensures that all transactions 
        assigned a ticket in batching have been executed. 
        """
        count = self.filter(batch_ticket=ticket, batch_status='UN_BATCHED').count()
        return count > 0 
    
    def get_next_txn(self, ticket, *args, **kwargs): 
        "Get the next transaction for processing."
        return self.filter(batch_ticket=self.ticket).exclude(
            batch_status=BaseObjectMixin.BatchStatus.BATCHED).first()
        

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

    batch_ticket = models.CharField(
        max_length=124, 
        blank=True, 
        null=True
        )

    batch_status = models.CharField(
        max_length=30,
        choices=BatchStatus.choices,
        default=BatchStatus.UN_BATCHED
    )

    # QuickBooks Fields
    qb_list_id = models.CharField(
        max_length=120, 
        blank=True, 
        null=True
    )
    qb_time_created = models.DateTimeField(blank=True, null=True)
    qb_time_modified = models.DateTimeField(blank=True, null=True)

    @staticmethod
    def get_query(*args, **kwargs): 
        """
        Returns QBXML the calling model should send to the web connector.
        """
        raise NotImplementedError
        
    @staticmethod
    def post_query(*args, **kwargs): 
        """
        Returns QBXML the calling model should send to the web connector.
        """
        raise NotImplementedError

    @staticmethod
    def patch_query(*args, **kwargs): 
        """
        Returns QBXML the calling model should send to the web connector.
        """
        raise NotImplementedError

    @staticmethod
    def process_get(*args, **kwargs): 
        """
        Handler for how the calling model should process the QBXML response from the web connector in the application
        """
        raise NotImplementedError

    @staticmethod
    def process_post(*args, **kwargs): 
        """
        Handler for how the calling model should process the QBXML response from the web connector in the application
        """
        raise NotImplementedError

    @staticmethod
    def process_patch(*args, **kwargs): 
        """
        Handler for how the calling model should process the QBXML response from the web connector in the application
        """
        raise NotImplementedError
    
    def batch_model(self, ticket, *args, **kwargs):
        """
        The inheriting model gets a batch_model() method that assigns the ticket number (batch_id)
        to the object. We can now batch all objects that have a ticket id and a 
        """
        self.batch_ticket = ticket
        self.save()

    # Sets the default model manager 
    objects = models.Manager()
    process = BaseObjectManager()


    class Meta: 
        abstract = True

    
class MessageLog(models.Model): 
    ticket = models.ForeignKey(
        TicketQueue,
        related_name='logs',
        on_delete=models.CASCADE
        )
    type = models.CharField(max_length=10)
    hresult = models.CharField(max_length=60, null=True, blank=True)
    message = models.TextField()
    created_on = models.DateTimeField(auto_now_add=True)

    def __str__(self): 
        return self.message
