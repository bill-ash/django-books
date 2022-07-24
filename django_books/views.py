import logging
import pandas as pd 

from datetime import datetime 
from lxml import etree
from uuid import uuid4

from django.shortcuts import render
from django.contrib.auth import get_user_model
from spyne.decorator import rpc, srpc
from spyne.model.complex import Array, Unicode
from spyne.model.primitive import Integer, String
from spyne.service import ServiceBase

from django_books.objects import *
from django_books.models import ServiceAccount, TicketQueue


logger = logging.getLogger(__name__)

class QBWC_CODES:
    """
    Response codes from webconnector
    """
    NONE = 'none'  # no work to do for the service
    BUSY = 'busy'  # service is busy with other task
    NVU = 'nvu'  # invalid user is sent to the service
    CC = ''  # indicates current company to use for the web connector to proceed further
    CONN_CLS_OK = 'ok'  # indicates web connector and web service _set_connection closed successfully
    CONN_CLS_ERR = 'done'  # indicates web connector failed connecting to web service and finished its job
    INTR_DONE = 'done'  # indicates web connector finished interactive session with web service
    UNEXP_ERR = 'unexpected error'  # unexpected error received from web connector
    CV = ''  # no update needed for web connector to update its version, it can proceed further


class QuickBooksService(ServiceBase): 

    @rpc(Unicode, Unicode, _returns=Array(Unicode))
    def authenticate(ctx, strUserName, strPassword):
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
            # Create a service account and make sure the username matches the UUID passed to the 
            # <UserName> </UserName> field in the .qwc file installed to WebConnector.
            if ServiceAccount.objects.get(qbid=strUserName).password == strPassword:
                logger.debug('Successfully logged in')
                
                # If there is new work to be processed check for it here. 
                if TicketQueue.objects.filter(status='1').count() > 0: # Created
                    ticket = TicketQueue.objects.filter(status='1').first().ticket
                    logger.debug('Processing Tickets...')

                    return [str(ticket), '']
                else:
                    logger.debug('No tickets in queue...')
                    
                    return ['none', 'none']
        return []
        
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
        
        if hresult:
            logger.debug("hresult=" + hresult)
            logger.debug("message=" + message)
        
        try:
            resp = process_response(response)
            resp_query = process_query_response(response)

        except Exception as e:
            logger.error(e)
            resp = {}

        # breakpoint()

        ticket = TicketQueue.objects.get(ticket=ticket)
        ticket_model = ticket.get_model()
        
        if ticket.method == 'GET': 
            try:
                ticket_model.get_response(resp_query)
                # success
                ticket.status = '4'
                ticket.save()
            
            except Exception as e:
                print(e)
                # failed
                ticket.status = '3'
                ticket.save()

        if ticket.method == 'POST': 
            try:
                print('\n'*4)
                logger.debug('Updating bill ref number')
                print('\n'*4)
                
                assert True == ticket_model.post_response(resp_query)
                if ticket_model.objects.filter(batch_id=str(ticket.ticket)).exclude(status='BATCH').count() >= 1: 
                    print('\n'*4)
                    logger.debug('more work to do')
                    print('\n'*4)
                    return 90 
                else: 
                    # success
                    print('\n'*4)
                    logger.debug('complete work success')
                    print('\n'*4)
                    ticket.status = '4'
                    ticket.save()
                    return 100 

            except Exception as e:
                print('\n'*4)
                logger.error('fail')
                print('\n'*4)
                ticket.status = '3'
                # ticket.save()
                print(e)
                return 100 

        # print('ERROR')
        if resp.get('statusSeverity') == 'Error' or hresult is not None:
            pass
            # error = Expense.objects.filter(status='APPROVED').first()
            # error.status = 'CLOSED'
            # error.save()
        else: 
            pass
            # success = Expense.objects.filter(status='APPROVED').first()
            # success.status = 'CLOSED'
            # success.save()

        # if the calling ticket has additional work to be completed... 
        # if ticket_model.objects.filter(batch_id=str(ticket.ticket), status='CLOSED').count() > 0:
        # # return session_manager.process_response(ticket, response, hresult, message)
            return 90
        return 100

    @srpc(Unicode, Unicode, Unicode, Unicode, Integer, Integer, _returns=String)
    def sendRequestXML(ticket, strHCPResponse, strCompanyFileName, qbXMLCountry, qbXMLMajorVers, qbXMLMinorVers):
        logger.debug('sendRequestXML() has been called')
        logger.debug('ticket:', ticket)
        logger.debug('strHCPResponse', strHCPResponse)
        logger.debug('strCompanyFileName', strCompanyFileName)
        logger.debug('qbXMLCountry', qbXMLCountry)

        ticket = TicketQueue.objects.get(ticket=ticket)
        model = ticket.get_model()

        # breakpoint()
        # from expenses.models import Expense 
        
        if ticket.method == 'GET':
            qbxml = model.get()
        else: 
            print('sending request.......')
            qbxml = model.post(str(ticket.ticket))
            print('\n'*4)
            logger.debug(qbxml)
            print('\n'*4)
        return qbxml

    @srpc(Unicode, _returns=Unicode)
    def clientVersion(strVersion, *args, **kwargs):
        """
        Check the current WebConnector version is compatiable with the application.

        Args:
            strVersion (str): QBWC version?
        """
        # print(type(ctx))
        # print(*args)
        # print(**kwargs)
        if strVersion == '2.3.0.207':
            print('Success!')
        # breakpoint()
        logger.debug('requesting auth')
        logger.debug('clientVersion(): version=%s' % strVersion)
        return ''


    @rpc(Unicode, _returns=Unicode)
    def closeConnection(ctx, ticket): 
        """
        Close the current connection with QuickBooks Webconnector.

        Args:
            ctx (DjangoHttpMethodContext): spyne processed request wasdl
            ticket (str): ticket that is completed?
        """
        logger.debug('closeConnection(): ticket=%s' % ticket)
        # This is where we can clean up any work 
        # realm = session_manager.get_realm(ticket)
        # session_manager.close_session(realm)
        return 'ok'

    
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
        logger.debug('connectionError(): ticket=%s, hresult=%s, message=%s' % (ticket, hresult, message))
        # realm = session_manager.get_realm(ticket)
        # session_manager.close_session(realm)
        return 'done'

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
        # In the case of expenses, errors should be wrapped in some try logic and displayed on completion 
        # of the work being preformed -- would not get batched. 
        logger.debug('getLastError(): ticket=%s' % ticket)


    @srpc(Unicode, _returns=Unicode)
    def getServerVersion(ticket): 
        """
        Provide a way for web-service to notify web connector of it’s version and other details about version
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string message string describing the server version and any other information that user may want to see
        """

        # Don't remember reading about this -- not sure if it's required
        version ='2.2.0.34'

        logger.debug('getServerVersion(): version=%s' % version)
        return version

    @srpc(Unicode, _returns=Unicode)
    def interactiveDone(ticket): 
        """
        Allow the web service to indicate to web connector that it is done with interactive mode.
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @return string value "Done" should be returned when interactive session is over
        """
        # for completeness - don't intend on using 
        logger.debug('interactiveDone(): ticket=%s' % ticket)
        return 'done'
        
    @rpc(Unicode, Unicode, _returns=Unicode)
    def interactiveRejected(ctx, ticket, reason):
        """
        Allow the web service to take alternative action when the interactive session it requested was
        rejected by the user or by timeout in the absence of the user.
        @param ticket the ticket from web connector supplied by web service during call to authenticate method
        @param reason the reason for the rejection of interactive mode
        @return string value "Done" should be returned when interactive session is over
        """
        logger.debug('interactiveRejected()')
        logger.debug(ticket)
        logger.debug(reason)
        return 'Interactive mode rejected'

 
    @srpc(Unicode, Unicode, _returns=Unicode)
    def interactiveUrl(ticket, sessionID):
        logger.debug('interactiveUrl')
        logger.debug(ticket)
        logger.debug(sessionID)
        return ''




def support(request):
    return render(request, 'django_books/support.html', {})

