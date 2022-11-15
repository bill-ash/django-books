# These are methods that should be implemented on the client side
# App user wants to implement a customer:
# - get_query() -> returns qbxml to query customers
# - post_query() -> returns qbxml to create a new customer in QB
# - patch_query() -> returns qbxml to update a customer in QB

from datetime import datetime
from lxml import etree


def query(model):
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <%sQueryRq requestID="1"> 
                </%sQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """ % (
        model,
        model,
    )
    return reqXML


def query_account():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <AccountQueryRq requestID="1">
                    <ActiveStatus>All</ActiveStatus> 
                </AccountQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_expense_account():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <AccountQueryRq requestID="1">
                    <AccountType>Expense</AccountType>
                </AccountQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_credit_card_account():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <AccountQueryRq requestID="1">
                    <AccountType>CreditCard</AccountType>
                </AccountQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_customer():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <CustomerQueryRq requestID="1">
                </CustomerQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_other_name_list():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <OtherNameQueryRq requestID="1">
                </OtherNameQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_vendor():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <VendorQueryRq requestID="1">
                </VendorQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML
 

def query_journal():
    # failed
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <JournalQueryRq requestID="1">
                </JournalQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML



def query_bill():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <BillQueryRq requestID="1">
                </BillQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_custom_txn():
    # https://github.com/IntuitDeveloper/QBXML_SDK_Samples/blob/64bitUpgrade/xmlfiles/legacy/CustomDetailReport.xml
    # does not get parsed all the way
    reqXML = """
       <?qbxml version="2.0"?>
        <QBXML>
        <!-- onError may be set to continueOnError or stopOnError-->
        <QBXMLMsgsRq onError="continueOnError">
            <CustomDetailReportQueryRq requestID = "UUIDTYPE">
            <CustomDetailReportType>CustomTxnDetail</CustomDetailReportType>
            <ReportDateMacro>ThisMonth</ReportDateMacro>
            <ReportAccountFilter>
                <AccountTypeFilter>AccountsReceivable</AccountTypeFilter>
            </ReportAccountFilter>
            <SummarizeRowsBy>Account</SummarizeRowsBy>
            <IncludeColumn>TxnNumber</IncludeColumn> 
            <IncludeColumn>TxnType</IncludeColumn> 
            <IncludeColumn>Amount</IncludeColumn> 
            </CustomDetailReportQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def query_class():
    reqXML = """
        <?qbxml version="15.0"?>
            <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <ClassQueryRq requestID="1">
                </ClassQueryRq>
            </QBXMLMsgsRq>
        </QBXML>
    """
    return reqXML


def add_customer(name="bill"):
    if name is None:
        raise ValueError("Name is a required field")
    name = name + datetime.now().strftime("%H%s")
    reqXML = """
        <?qbxml version="15.0"?>
        <QBXML>
            <QBXMLMsgsRq onError="stopOnError">
                <CustomerAddRq>
                    <CustomerAdd><Name>{}</Name></CustomerAdd>
                </CustomerAddRq> 
            </QBXMLMsgsRq>
        </QBXML>
        """.format(
        name
    )
    return reqXML


def add_credit_card_payment(
    credit_card="CalOil Card",
    vendor="ODI",
    date="2022-01-01",
    ref_number="3123",
    memo="MEMO",
    expense_account="",
    amount=102.12,
    expense_description="",
):

    reqXML = f"""
    <?qbxml version="15.0"?>
    <QBXML>
    <QBXMLMsgsRq onError="stopOnError">
        <CreditCardChargeAddRq>
            <CreditCardChargeAdd> 
            <AccountRef>                                         
                <FullName>{credit_card}</FullName>
            </AccountRef>

            <PayeeEntityRef>
                <FullName >{vendor}</FullName>
            </PayeeEntityRef>
            
            <TxnDate >{date}</TxnDate> 
            <RefNumber >{ref_number}</RefNumber>
            <Memo >{memo}</Memo> 
            
            <ExpenseLineAdd> 
                <AccountRef> 
                    <FullName >{expense_account}</FullName>
                </AccountRef>
                <Amount >{amount}</Amount> 
                <Memo >{expense_description}</Memo> 
            </ExpenseLineAdd>
                    
            </CreditCardChargeAdd>
    </CreditCardChargeAddRq>
    </QBXMLMsgsRq>
    </QBXML>
    """

    return reqXML


def process_response(response):

    qbxml_root = etree.fromstring(response)

    assert qbxml_root.tag == "QBXML"

    qbxml_msg_rs = qbxml_root[0]

    assert qbxml_msg_rs.tag == "QBXMLMsgsRs"

    response_body_root = qbxml_msg_rs[0]

    assert "statusCode" in response_body_root.attrib

    return response_body_root


def process_query_response(response):

    response_body_root = process_response(response)

    resp = []
    for x in range(len(response_body_root)):
        children = response_body_root[x].getchildren()
        tmp = {}
        for child in children:
            tmp[child.tag] = child.text
        resp.append(tmp)

    return resp
