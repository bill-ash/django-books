# Django Books

Functional django application for interacting with the QuickBooks Desktop Webconnector (QBWC).

Find example applications in `/examples/`.

## Install 

Install the latest version from github: 

```
python -m pip install git+httsp://github.com/bill-ash/django-books
```

or from pip using: 

```
python -m pip --upgrade django-books
```

## Examples 

Two sample apps are included for adding new customers and jobs as well as creating expenses via credit-card charges.


## TODOS

Create a service account which is responsible for communicating with the QBWC. 
- Add a method that produces a `.qwc` file that is installed to QBWC
- Like an admin? Maybe a profile page for an admin that will spit out a .qwc file?

Abstracting models is difficult. Each application will have it's own unique workflows that depend 
on business requirements. 

Create a model mixin that will add new 'batches' to be added to a ticket queue. The ticket 
queue is the work to be preformed on the next web connector sync. 

Ticket log for syncing QB data with external resources/dashboards is different from importing new records 
from django. 

## Resources 

Heavily inspired by previous attempts at talking to Quick Books desktop with the goal of using 
python3 and current django version and no redis dependency. 

- https://github.com/weltlink/django-quickbooks 
- https://github.com/BillBarry/pyqwc
- http://spyne.io/#inprot=HttpRpc&outprot=JsonDocument&s=rpc&tpt=WsgiApplication&validator=true

Intuit documentation is quite dated but still useful. 

- https://developer.intuit.com/app/developer/qbdesktop/docs/develop/sample-applications-and-code
- https://github.com/IntuitDeveloper/QBXML_SDK_Samples/tree/64bitUpgrade/xmlfiles
- https://developer.intuit.com/app/developer/qbdesktop/docs/api-reference/qbdesktop

Program guide with detailed outline of all the required endpoints for communicating with the 
web connector. 

- https://static.developer.intuit.com/qbSDK-current/doc/pdf/QBWC_proguide.pdf


Additionally, the forums are somewhat active: 

- https://help.developer.intuit.com/s/


## Notes 

A single application will work on many QB files. 

- Associate an app with a specific QB file. 


Usernames (service accounts) are associated with specific files (a list of files). Test the authing 


