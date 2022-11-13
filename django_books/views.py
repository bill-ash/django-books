from ast import Interactive
import logging 

from datetime import datetime 
from lxml import etree
from uuid import uuid4

from django.shortcuts import render
from django.contrib.auth import get_user_model
from spyne.decorator import rpc, srpc
from spyne.model.complex import Array, Unicode
from spyne.model.primitive import Integer, String
from spyne.service import ServiceBase

from django_books.objects import process_response, process_query_response
from django_books.models import ServiceAccount, TicketManager, TicketQueue # MessageLog,

from django.conf import settings

logger = logging.getLogger(__name__)

class QBWC_CODES:
    """
    Response codes from webconnector
    """
    # no work to do for the service
    NONE = 'none'  
    
    # service is busy with other task
    BUSY = 'busy'  
    
    # invalid user is sent to the service
    INVALID_USER = 'nvu'  
    
    # indicates current company to use for the web connector to proceed further
    CURRENT_COMPANY = ''  
    
    # indicates web connector and web service _set_connection closed successfully
    CONN_CLOSE_OK = 'ok'  
    
    # indicates web connector failed connecting to web service and finished its job
    CONN_CLOSE_ERROR = 'done'  
    
    # indicates web connector finished interactive session with web service
    INTERACTIVE_COMPLETE = 'done'  
    
    # unexpected error received from web connector
    UNEXPECTED_ERROR = 'unexpected error'  
    
    # no update needed for web connector to update its version, it can proceed further
    CURRENT_VERSION = ''  


class QuickBooksService(ServiceBase): 

    @srpc(Unicode, Unicode, _returns=Array(Unicode))
    def authenticate(strUserName, strPassword):
        """
        Authenticate with QuickBooks WebConnector. 
        Return value schedule: 
         - No work to be preformed: 
            - ['none', 'none']
         - Pending request: session token of work to reference and the current open company file  
            - ['guid', ''] 
            - ['guid', 'path/to/file_name.qbo'] 
         - Invalid user - not authenticated
            - ['', ''] | ['nvu', 'nvu']

        Args:
        @rpc >> ctx (DjangoHttpMethodContext): spyne.server.django.DjangoHttpMethodContext Inspect the information 
        returned to be parsed by spyne from the webconnector.
        The ctx (djangoHttpMethodContext) returns the method call of the webconnector as well as the parsed xml
            strUsername (str): Username to authenticate against. Needs to match realm id passed 
            when creating qbwc app installed.
            strPassword (str): Password to match against realm password
        """
        
        if ServiceAccount.objects.get(qbid=strUserName):
            if ServiceAccount.objects.get(qbid=strUserName).password == strPassword:
                logger.debug('Successfully logged in')
                
                
                if TicketQueue.process.count_queue() > 0: 
                    ticket = TicketQueue.process.get_next_ticket()
                    logger.debug('Processing Tickets...')
                    return [ticket, QBWC_CODES.CURRENT_COMPANY]

                else:
                    logger.debug('No tickets in queue...')
                    return [QBWC_CODES.NONE, QBWC_CODES.NONE]
        
        logger.error('Invalid user')
        return [QBWC_CODES.INVALID_USER, QBWC_CODES.INVALID_USER]


    @srpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer, _returns=String) #Unicode, Unicode, Unicode,
    def sendRequestXML(ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers): 
        
        logger.debug('sendRequestXML() has been called')
        logger.debug('ticket: ' + ticket)
        logger.debug('strCompanyFileName ' + str(strCompanyFileName))
        
        current_ticket = TicketQueue.objects.get(ticket=ticket)
        # message = MessageLog()
        # message.ticket = current_ticket 
                
        model = current_ticket.get_model()
   
        if current_ticket.method == 'GET':
            qbxml = model.get_query()
            logger.debug(qbxml)

        elif current_ticket.method == 'POST': 
            qbxml = model.post_query(current_ticket.ticket)
            logger.debug(qbxml)

        else:
            qbxml = model.patch_query()
            
        current_ticket.status = TicketQueue.TicketStatus.PROCESSING
        current_ticket.save()
        # message.save()

        return qbxml
        
    @srpc(Unicode, Unicode, Unicode, Unicode, _returns=Integer)
    def receiveResponseXML(ticket, response, hresult, message): 
        """
        Returns the data response form the QuickBooks WebConnector. 

        Args:
            ticket (str): ticket
            response (QBXML): Response from QuickBooks
            hresult (str): Hex error message that could accompany any successful work 
            message (str): Error message 
        
        @return (int) Positive integer 100 for completed work, and less than 100 to move to the next ticket. 
            Needs to be handled by the session manager.  
        """

        logger.debug('receiveResponseXML()')
        logger.debug("ticket=" + ticket)
        logger.debug("response=" + response)
        
        # Check to see if there is an error message
        if hresult:
            logger.error("hresult=" + hresult)
            logger.error("message=" + message)
                
        try:
            # Process the response from QuickBooks - should this be model dependent?
            response_code = process_response(response).get('statusSeverity')
            qb_response = process_query_response(response)

        except Exception as e:
            logger.error(str(e))
            response_error = {}
        
        current_ticket = TicketQueue.objects.get(ticket=ticket)
        model = current_ticket.get_model()
        
        
        if current_ticket.method == current_ticket.TicketMethod.GET: 
            try:
                # Assumes GET method is a single round trip...
                logger.debug('Processing GET query response')
                model.process_get(qb_response, ticket)
                current_ticket.status = current_ticket.TicketStatus.SUCCESS
                current_ticket.save()
            
            except Exception as e:
                logger.error(str(e))
                current_ticket.status = current_ticket.TicketStatus.FAILED
                current_ticket.save()

        elif current_ticket.method == current_ticket.TicketMethod.POST: 
            try:
                logger.debug('Processing POST query response')
                # Errors get handled in processing function and bubble to { getLastError() }
                model.process_post(qb_response, ticket)
                
                # breakpoint()
                # model.objects.filter(batch_ticket=ticket).exclude(batch_status='BATCHED').count()
                if model.process.check_for_work(ticket):
                    logger.debug('More work to do')
                    return 90 
                else: 
                    logger.debug('Work completed')
                    current_ticket.status = current_ticket.TicketStatus.SUCCESS
                    current_ticket.save()
                    return 100 

            except Exception as e:
                # Don't try to handle exception end the operation 
                logger.error(str(e))
                current_ticket.status = current_ticket.TicketStatus.ERROR
                raise Exception 
                # return 100 
        else: 
            try: 
                logger.debug('Processing PATCH query response')

            except Exception as e: 
                logger.error(str(e))
                raise Exception('Error in PATCH process response')


        if response_code == 'Error' or hresult is not None:
            # Errors should be logged and continued upon?
            pass
        else: 
            pass
        return 100

    @srpc(Unicode, _returns=Unicode)
    def serverVersion(strVersion, *args): 
        """
        Provide a way for web-service to notify web connector of it’s version and other details about version
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string message string describing the server version and any other information that user may want to see
        """
        version=settings.QBWC_VERSION
        logger.debug(f'getServerVersion(): version={version}')
        return version

    
    @srpc(Unicode, _returns=Unicode)
    def clientVersion(strVersion, *args, **kwargs):
        """
        Check the current WebConnector version is compatiable with the application.

        Args:
            strVersion (str): QBWC Version
        """
        if strVersion == settings.QBWC_VERSION:
            logger.debug('Matches current version')
        logger.debug(f'clientVersion(): version={strVersion}')
        
        return QBWC_CODES.CURRENT_VERSION


    @rpc(Unicode, _returns=Unicode)
    def closeConnection(ctx, ticket): 
        """
        Close the current connection with QuickBooks Webconnector.
        This is where we can clean up any work 

        Args:
            ctx (DjangoHttpMethodContext): spyne processed request wasdl
            ticket (str): ticket that is completed?
        """
        # breakpoint()
        logger.debug(f'closeConnection(): ticket={ticket}')
        # return QBWC_CODES.CONN_CLOSE_OK
        return f'Completed Operation: {ticket}'

    
    @srpc(Unicode, Unicode, Unicode, _returns=Unicode)
    def connectionError(ticket, hresult, message): 
        """
        Tell the web service about an error the web connector encountered in its attempt to connect to QuickBooks
        or QuickBooks POS
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @param hresult the HRESULT (in HEX) from the exception thrown by the request processor
        @param message The error message that accompanies the HRESULT from the request processor
        @return string value "done" to indicate web service is finished or the full path of the different company for
        retrying _set_connection.
        """
        # log = MessageLog(
        #     type = 'error', 
        #     hresult = hresult, 
        #     message = str(logger.debug(f'connectionError(): ticket={ticket}, hresult={hresult}, message={message}'))
        # )
        # log.save()

        logger.debug(f'connectionError(): ticket={ticket}, hresult={hresult}, message={message}')
        
        current_ticket = TicketQueue.objects.get(ticket=ticket)
        current_ticket.status = TicketQueue.TicketStatus.ERROR

        return QBWC_CODES.CONN_CLOSE_ERROR

    @srpc(Unicode, _returns=Unicode)
    def getLastError(ticket): 
        """
        Allow the web service to return the last web service error, normally for displaying to user, before
        causing the update action to stop.
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string message describing the problem and any other information that you want your user to see.
        The web connector writes this message to the web connector log for the user and also displays it in the web
        connector’s Status column.
        """
        # breakpoint()
        # log = MessageLog(
        #     ticket=TicketQueue.objects.get(ticket=ticket),
        #     type = 'error',
        #     hresult = '',
        #     message = f'getLastError(): ticket={ticket}'
        # )
        # log.save()
        
        logger.error(f'getLastError(): ticket={ticket}')
        return f'Error processing ticket: {ticket}'


 
    # @srpc(Unicode, _returns=Unicode)
    # def interactiveDone(ticket): 
    #     """
    #     Allow the web service to indicate to web connector that it is done with interactive mode.
    #     @param ticket the ticket from web connector supplied by web service during call to authenticate method
    #     @return string value "Done" should be returned when interactive session is over
    #     """
    #     # for completeness - don't intend on using 
    #     logger.debug('interactiveDone(): ticket=%s' % ticket)
    #     return 'done'
        
    # @rpc(Unicode, Unicode, _returns=Unicode)
    # def interactiveRejected(ctx, ticket, reason):
    #     """
    #     Allow the web service to take alternative action when the interactive session it requested was
    #     rejected by the user or by timeout in the absence of the user.
    #     @param ticket the ticket from web connector supplied by web service during call to authenticate method
    #     @param reason the reason for the rejection of interactive mode
    #     @return string value "Done" should be returned when interactive session is over
    #     """
    #     logger.debug('interactiveRejected()')
    #     logger.debug(ticket)
    #     logger.debug(reason)
    #     return 'Interactive mode rejected'

 
    # @srpc(Unicode, Unicode, _returns=Unicode)
    # def interactiveUrl(ticket, sessionID):
    #     logger.debug('interactiveUrl')
    #     logger.debug(ticket)
    #     logger.debug(sessionID)
    #     return ''




def support(request):
    return render(request, 'django_books/support.html', {})

