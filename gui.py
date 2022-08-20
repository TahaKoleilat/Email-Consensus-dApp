#! python3
# gui.py
# Provides the user interface elements for the P.O.C application.

import pyperclip, re, datetime
import tkinter as tk
from tkinter import ttk

from tkinter import scrolledtext
from tkinter import ttk

from .message import Request, Response, Bundle
from .api import GmailAPI
from .stateSingleton import StateSingleton
from .blockchain import BundleBlock, RequestBlock
from .addressParser import AddressParser

# ---------- Global values ---------- #
emailRegex = re.compile(r"\w+@\w+?\.com")

def pad_tl(v): # pad top/left
    return (v, 0)

def pad_br(v): # pad bottom/right
    return (0, v)

# ---------- Parent GUI class ---------- #
class BaseFrame(tk.Frame):
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        tk.Frame.__init__(self, parent)
        self.pack() # as long as the BaseFrame calls this, inheritors don't need to do it themselves

        # Get our singleton state variable
        self.globals = StateSingleton()
        self.globals.responses = {}
        self.globals.recipients = None
        self.globals.request = None
        
        # Configure application styles
        self.style = ttk.Style(self)
        self.style.configure('TLabel', font=('Helvetica', 11))
        self.style.configure('TButton', font=('Helvetica', 11))

    def switchToResponseSearchPage(self, callerSelf, requestValue, hideOtherSelf=None):
        '''
        Arguments:
            self -- Not used, just needed for BaseFrame storing.
            callerSelf -- The self of the calling instance to hide.
            requestValue -- list containing four items with the format:
                            [subjectString, senderString, dateString, emailID, recipientsString].
            hideOtherSelf -- (OPTIONAL) Another self to hide.
        '''
        
        # Hide caller
        callerSelf.pack_forget()

        # Hide other self if relevant
        if hideOtherSelf != None:
            hideOtherSelf.pack_forget()
        
        # Set up the tally page
        self.globals.responseSearchPage.update(requestValue)
        self.globals.responseSearchPage.pack()
    
    def switchToValidRequestRecipientSearch(self, callerSelf, emailAddress, expiryDate, hideOtherSelf=None):
        '''
        Arguments:
            self -- Not used, just needed for BaseFrame storing.
            callerSelf -- The self of the calling instance to hide.
            emailAddress -- Email address to find a response from.
            hideOtherSelf -- (OPTIONAL) Another self to hide.
        '''
        
        # Hide caller
        callerSelf.pack_forget()

        # Hide other self if relevant
        if hideOtherSelf != None:
            hideOtherSelf.pack_forget()

        # Set up the recipient search page
        self.globals.validRequestRecipientSearch.update(emailAddress, expiryDate)
        self.globals.validRequestRecipientSearch.show()

class GUI(BaseFrame):
    def __init__(self, parent, blockchain, CREDENTIALS_DIR):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        self.globals.root = self
        
        # Make credentials a globally accessible value
        self.globals.CREDENTIALS_DIR = CREDENTIALS_DIR
        
        # Make blockchain a globally accessible value
        assert type(blockchain).__name__ == "LocalBlockchain"
        self.globals.blockchain = blockchain
        
        # FRAME ROW 1: Home butons
        row1 = tk.Frame(self)
        requestButton = ttk.Button(
            row1,
            text = 'Make a Request',
            width = 25,
            command = lambda: (
                self.request.pack(),
                self.response.pack_forget(),
                self.commitBundle.pack_forget(),
                self.createBundle.pack_forget()
            )
        )
        responsesButton = ttk.Button(
            row1,
            text = 'Check Responses',
            width = 25,
            command = lambda: (
                self.response.pack(),
                self.request.pack_forget(),
                self.commitBundle.pack_forget(),
                self.createBundle.pack_forget()
            )
        )
        commitButton = ttk.Button(
            row1,
            text = 'Commit Bundle',
            width = 25,
            command = lambda: (
                self.commitBundle.pack(),
                self.request.pack_forget(),
                self.response.pack_forget(),
                self.createBundle.pack_forget()
            )
        )
        requestButton.pack(side="left"); responsesButton.pack(side="left"); commitButton.pack(side="left"); row1.pack()
        
        # CONTROL: Create the screens we'll navigate between
        self.request = RequestScreen(self)
        self.response = ResponseScreen(self)
        self.createBundle = CreateBundleScreen(self)
        self.commitBundle = CommitBundleScreen(self)

        # Place the screens for navigation between
        self.response.pack()
        self.request.pack(); self.request.pack_forget() # Hide by default
        self.createBundle.pack(); self.createBundle.pack_forget() # Hide by default
        self.commitBundle.pack(); self.commitBundle.pack_forget() # Hide by default
           
    def show_create_bundle(self):
        self.createBundle.pack()
    
    def show_commit_bundle(self):
        self.commitBundle.pack()
    
    def show_response(self):
        self.response.pack()

# ---------- Screen 1: Request creation ---------- #
class RequestScreen(BaseFrame):
    '''
    Provides an option menu to select what action is being requested,
    and a text input area to type in the message. A button allows a request
    to be formatted that can be pasted into an email.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        
        # Dropdown state
        actionOptions = ["Approval"]
        action = tk.StringVar(self)
        action.set(actionOptions[0])
        
        expiryOptions = ["Days", "Hours", "Minutes"]
        self.expiryOpt = tk.StringVar(self)
        self.expiryOpt.set(expiryOptions[0])
        
        # Entry state
        def isOkay(outcome):
            '''
            Performs ttk validation of the expiry entry field to prevent excess input >3.
            Outcome (%P) will be the string if the change is allowed to occur.
            '''
            if len(outcome) > 3:
                return False
            elif len(outcome) != 0:
                try:
                    int(outcome)
                except:
                    return False
            return True
        self.entryValue = tk.StringVar(self)
        self.entryValue.set("1")
        okayCommand = self.register(isOkay)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        ENTRY_WIDTH=5
        BOX_WIDTH=60

        # FRAME ROW 1: Menu to set action and expiry length
        row1 = tk.Frame(self)
        
        ## ROW 1.1: Action specification
        actionLabel = ttk.Label(row1, text='Action:'); actionLabel.pack(side="left", padx=PAD_X)
        actionDropdown = ttk.OptionMenu(row1, action, "", *actionOptions, command=lambda selection: action.set(selection)); actionDropdown.pack(side="left", padx=PAD_X)
        
        ## ROW 1.2: Expiry specification
        expiryLabel = ttk.Label(row1, text='Expiry Limit:'); expiryLabel.pack(side="left", padx=PAD_X)
        expiryEntry = ttk.Entry(row1, validate="all", validatecommand=(okayCommand, "%P"), textvariable = self.entryValue, width=ENTRY_WIDTH); expiryEntry.pack(side="left", padx=PAD_X)
        expiryDropdown = ttk.OptionMenu(row1, self.expiryOpt, "", *expiryOptions, command=lambda selection: self.expiryOpt.set(selection)); expiryDropdown.pack(side="left", padx=PAD_X)
        
        row1.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))

        # FRAME ROW 2: Content section to write the request
        requestLabel = ttk.LabelFrame(self, text="Write your request here"); requestLabel.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        requestEntry = scrolledtext.ScrolledText(requestLabel, width=BOX_WIDTH); requestEntry.pack()

        # FRAME ROW 3: Button to copy a format to clipboard
        copyButton = ttk.Button(self, text='Copy Request', command=lambda: self.create_request(requestEntry.get('1.0', tk.END), action))
        copyButton.pack(padx=PAD_X, pady=PAD_Y)
        
        # FRAME ROW 4: Creation success / failure label
        self.successMessage = tk.StringVar(self)
        successLabel = ttk.Label(self, textvariable=self.successMessage); successLabel.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        
        self.globals.requestScreen = self
        
    def create_request(self, messageContents, action):
        # Strip out newlines
        "Newlines aren't supported by the Request class"
        messageContents = messageContents.replace("\r", "").replace("\n", " ") # Crude but it'll do for P.O.C.
        
        # Validate that fields are not empty
        if len(self.entryValue.get()) == 0:
            self.successMessage.set("Expiry limit must be set!")
            return
        else:
            self.successMessage.set("")
            
        if len(messageContents) < 5 or messageContents == None:
            self.successMessage.set("Message must be set!")
            return
        else:
            self.successMessage.set("")
        
        # Format the expiry length
        if self.expiryOpt.get() == "Days":
            expiryLength = "{0}d".format(self.entryValue.get())
        elif self.expiryOpt.get() == "Hours":
            expiryLength = "{0}h".format(self.entryValue.get())
        else:
            expiryLength = "{0}m".format(self.entryValue.get())
                
        # Create request
        request = Request(expiryLength)
        request.create_new(messageContents, action.get().lower())
        
        # Write request to blockchain
        '''
        This section is newly added to conform to changes for "Proof of
        Consistent Delivery" in the report. In short, once a user creates
        a Request, it's immediately added to the blockchain.
        Propagation of this block is outside the scope of the consensus
        protocol, however.
        '''
        block = RequestBlock(request, self.globals.blockchain.get_last_block().hash)
        self.globals.blockchain.add_block(block)
        self.globals.blockchain.save()
        
        # Copy to clipboard
        pyperclip.copy(request.format_request_as_string())

# ---------- Screen 2: Response handling ---------- #
class ResponseScreen(BaseFrame):
    '''
    Serves as the parent screen between which request search and response search
    can be alternated between.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)

        # CONTROL: Create the screens we'll navigate between
        self.search = RequestSearchPage(self)
        self.tally = ResponseSearchPage(self)
        self.results = RequestResultsPage(self)

        self.tally.pack()
        self.tally.pack_forget() # Hide by default
        
        self.results.pack()
        self.results.pack_forget() # Hide by default

        self.search.pack() # Leave visible by default
        
        self.globals.responseScreen = self
    
    def show(self):
        self.pack()
        self.show_search() # This is default behaviour
    
    def show_tally(self):
        self.search.hide() # requestSearchPage
        self.results.hide() # requestResultsPage
        self.tally.show() # responseSearchPage
    
    def show_search(self):
        self.tally.hide() # responseSearchPage
        self.results.hide() # requestResultsPage
        self.search.show() # requestSearchPage
    
    def show_results(self):
        self.tally.hide() # responseSearchPage
        self.search.hide() # requestSearchPage
        self.results.show() # requestResultsPage
    
    def hide(self):
        self.pack_forget()
        self.search.hide() # requestSearchPage
        self.tally.hide() # responseSearchPage
        self.results.hide() # requestResultsPage

# ---------- Screen 2.1: Find the request ---------- #
class RequestSearchPage(BaseFrame):
    '''
    Provides search functionality to find a request email to process.
    Search results will be shown in a table, from which a row can be selected
    to proceed to response search.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        ENTRY_WIDTH=75

        # Label above the search bar
        searchLabel = ttk.Label(self, text='Search for Request'); searchLabel.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))

        # FRAME ROW 2: Search bar with button
        row2 = tk.Frame(self)
        searchBar = ttk.Entry(row2, width=ENTRY_WIDTH); searchBar.pack(side="left", padx=pad_br(PAD_X))
        searchButton = ttk.Button(row2, text="Search", command=lambda: self.search_for_requests(searchBar.get())); searchButton.pack(side="left")
        row2.pack(padx=PAD_X, pady=PAD_Y)
        
        self.globals.requestSearchPage = self
    
    def search_for_requests(self, query):
        # Prevent bad requests
        "It's not bad if I/someone does it, it's just bad because it may take a long time to resolve"
        if len(query) < 5:
            return
        
        # Perform the query
        apiClient = GmailAPI(self.globals.CREDENTIALS_DIR)
        searchResult = apiClient.search(query)
        
        # Pass results to our search display table and trigger its display
        self.globals.requestResultsPage.update(query, searchResult)
        self.hide()
        self.globals.requestResultsPage.show()
    
    def show(self):
        self.pack()
    
    def hide(self):
        self.pack_forget()

class RequestResultsPage(BaseFrame):
    '''
    Displays the results of Google API search as a table. Table rows can
    be double clicked to launch the handleDoubleClick() function which
    knows the row's contents that was clicked.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        TOTAL_WIDTH=520
        
        # Show search details
        self.query = tk.StringVar(self)
        
        queryLabel = ttk.Label(self, textvariable=self.query)
        queryLabel.pack(anchor="w", padx=PAD_X, pady=PAD_Y)
        
        # Format the table
        self.tree = ttk.Treeview(self, column=("Subject", "From", "Date"), show='headings')
        
        self.tree.column("#1", anchor=tk.CENTER, width=int((TOTAL_WIDTH*0.4)))
        self.tree.heading("#1", text="Subject")

        self.tree.column("#2", anchor=tk.CENTER, width=int(TOTAL_WIDTH*0.4))
        self.tree.heading("#2", text="From")

        self.tree.column("#3", anchor=tk.CENTER, width=int(TOTAL_WIDTH*0.2))
        self.tree.heading("#3", text="Date")

        self.tree.pack(padx=PAD_X)
        self.tree.bind("<Double-1>", self.handleDoubleClick)
        
        # Button to go back to Request search
        self.goBackButton = ttk.Button(
            self,
            text = 'Go Back',
            command = lambda: (
                self.pack_forget(),
                self.globals.requestSearchPage.show()
            )
        )
        self.goBackButton.pack(padx = PAD_X, pady = PAD_Y)
        
        self.globals.requestResultsPage = self
    
    def update(self, query, searchResult):
        '''
        Update the table's contents with search results.
        This will reset the table on search so results don't
        accumulate over sequential searches.
        
        Arguments:
            query -- A string that was used for the email API query.
            searchResult -- A list containing at least three items with the format:
                            [subjectString, senderSTring, dateString]. An additional
                            fourth value should usually exist (but won't be shown) which
                            is the email's ID.
        
        Credit to https://www.activestate.com/resources/quick-reads/how-to-display-data-in-a-table-using-tkinter/
        '''
        self.query.set("Email query: {0}".format(query))
        
        self.tree.delete(*self.tree.get_children()) # Wipe tree state
        for r in searchResult:
            self.tree.insert("", tk.END, values=r) # Populate tree with new results
    
    def handleDoubleClick(self, event):
        '''
        Credit to https://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
        '''
        
        # Get the row value that was clicked
        try:
            item = self.tree.selection()[0]
            requestValue = self.tree.item(item,"values")

            # Blank our global responses
            self.globals.responses = {}
        
            # Switch to the response search page and pass along the row value
            self.switchToResponseSearchPage(self, requestValue, self.globals.requestSearchPage)
        except:
            "If this happens, the user clicked a blank row, shouldn't be a big deal"
            pass
    
    def show(self):
        self.pack()
    
    def hide(self):
        self.pack_forget()

# ---------- Screen 2.2: List our responses ---------- #
class ResponseSearchPage(BaseFrame):
    '''
    This page controls the response search process. Once a valid Request has been
    selected, the user will be able to locate Responses formed for this Request
    using the elements and widgets controlled by this page.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        
        # Page state
        self.subject = tk.StringVar(self)
        self.sender = tk.StringVar(self)
        self.date = tk.StringVar(self)
        self.emailID = tk.StringVar(self)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        
        # FRAME ROW 1: Header label
        header = ttk.Label(self, text='Email Details')
        header.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # FRAME ROW 2: From state values
        row2 = tk.Frame(self)
        fromDescription = ttk.Label(row2, text="From:"); fromDescription.pack(side="left")
        fromLabel = ttk.Label(row2, textvariable=self.sender); fromLabel.pack(side="left", padx=pad_tl(PAD_X))
        row2.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # FRAME ROW 3: Date state values
        row3 = tk.Frame(self)
        dateDescription = ttk.Label(row3, text="Sent Date: "); dateDescription.pack(side="left")
        dateLabel = ttk.Label(row3, textvariable=self.date); dateLabel.pack(side="left", padx=pad_tl(PAD_X))
        row3.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # FRAME ROW 4: Subject state values
        row4 = tk.Frame(self)
        subjectDescription = ttk.Label(row4, text="Subject: "); subjectDescription.pack(side="left")
        subjectLabel = ttk.Label(row4, textvariable=self.subject); subjectLabel.pack(side="left", padx=pad_tl(PAD_X))
        row4.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # CONTROL: Valid request handling
        self.vReqWidget = ValidRequestWidget(self)
        self.vReqWidget.pack()
        self.vReqWidget.pack_forget()

        self.vReqSearch = ValidRequestRecipientSearch(self)
        self.vReqSearch.pack()
        self.vReqSearch.pack_forget()
        
        # Invalid request handling
        self.iReqWidget = InvalidRequestWidget(self)
        self.iReqWidget.pack()
        self.iReqWidget.pack_forget()

        self.globals.responseSearchPage = self
    
    def update(self, requestValue):
        '''
        Update this object's state so it knows the request value it's in charge of.
        
        Arguments:
            requestValue -- list containing four items with the format:
                            [subjectString, senderSTring, dateString, emailID].
        '''
        
        # Deconstruct value into variables
        subject, sender, date, emailID, recipients = requestValue
        
        # Set object state variables
        self.subject.set(subject)
        self.sender.set(sender)
        self.date.set(date)
        self.emailID.set(emailID)
        
        # Obtain the email message
        apiClient = GmailAPI(self.globals.CREDENTIALS_DIR)
        emailText = apiClient.read(emailID)
        
        # Parse it as a Request object
        request = Request()
        isValid = request.parse_from_email(emailText)
        
        # If Response suggests a valid Request was made, bring that up
        if isValid:
            # Make values available globally
            self.globals.recipients = recipients
            self.globals.request = request

            # Trigger an update to our widgets and their display status
            self.vReqWidget.update()
            self.globals.validRequestWidget.pack()
            self.globals.invalidRequestWidget.hide()
        # Otherwise, bring up the fail message
        else:
            # Reset any existing global values
            self.globals.recipients = None
            self.globals.request = None

            # Trigger change in our display states
            self.globals.invalidRequestWidget.pack()
            self.globals.validRequestWidget.pack_forget()

    def show(self):
        self.pack()
        self.vReqWidget.show()
        self.vReqSearch.hide()
    
    def hide_valid(self):
        self.pack_forget()
        self.vReqSearch.pack_forget()
        self.vReqWidget.pack_forget()
    
    def hide(self):
        self.pack_forget()
        self.vReqSearch.hide()
        self.vReqWidget.hide()
        self.iReqWidget.hide()

class ValidRequestWidget(BaseFrame):
    '''
    Displays the details of a Request that was made.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        
        # Widget state
        self.message = tk.StringVar(self)
        self.expiry = tk.StringVar(self)
        self.expected_response1 = tk.StringVar(self)
        self.expected_response2 = tk.StringVar(self)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        TOTAL_WIDTH=520
        
        # ROW 2: Request header message
        messageDescription = ttk.Label(self, text="Request Details")
        messageDescription.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # ROW 2: Display request message
        row2 = tk.Frame(self)
        messageDescription = ttk.Label(row2, text="Message: "); messageDescription.pack(side="left")
        messageLabel = ttk.Label(row2, textvariable=self.message); messageLabel.pack(side="left", padx=pad_tl(PAD_X))
        row2.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # ROW 3: Display action requested
        row3 = tk.Frame(self)
        actionDescription = ttk.Label(row3, text="Action requested: "); actionDescription.pack(side="left")
        actionLabel1 = ttk.Label(row3, textvariable=self.expected_response1); actionLabel1.pack(side="left", padx=pad_tl(int(PAD_X/2)))
        orLabel = ttk.Label(row3, text="OR"); orLabel.pack(side="left", padx=pad_tl(int(PAD_X/2)))
        actionLabel2 = ttk.Label(row3, textvariable=self.expected_response2); actionLabel2.pack(side="left", padx=pad_tl(int(PAD_X/2)))
        row3.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # FRAME ROW 4: Expiry state values
        row4 = tk.Frame(self)
        expiryDescription = ttk.Label(row4, text="Expiry: "); expiryDescription.pack(side="left")
        expiryLabel = ttk.Label(row4, textvariable=self.expiry); expiryLabel.pack(side="left", padx=pad_tl(PAD_X))
        row4.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # Display table to select responses to retrieve
        tree = ttk.Treeview(self, column=("Recipient", "Processed"), show='headings')
        
        tree.column("#1", anchor=tk.CENTER, width=int(TOTAL_WIDTH*0.5))
        tree.heading("#1", text="Recipient")

        tree.column("#2", anchor=tk.CENTER, width=int(TOTAL_WIDTH*0.5))
        tree.heading("#2", text="Processed")

        tree.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        tree.bind("<Double-1>", self.handleDoubleClick)
        self.tree = tree

        # Button to go back to Request search
        self.goBackButton = ttk.Button(
            self,
            text = 'Go Back',
            width = 25,
            command = lambda: (
                self.pack_forget(),
                self.globals.responseSearchPage.pack_forget(),
                self.globals.requestResultsPage.show())
        )
        self.goBackButton.pack(padx=PAD_X, pady=PAD_Y)
        
        self.globals.validRequestWidget = self
    
    def update(self):
        '''
        Update this object's state so it knows the original Request's message
        and its expected actions/responses. Also, let it know the recipients
        of the Request so it can format a table to display these for
        subsequent searches to take place.
        '''
        
        # Set object state variables
        self.message.set(self.globals.request.message)
        self.expiry.set(self.globals.request.expiry)
        
        _expected_responses = self.globals.request.get_expected_responses()
        self.expected_response1.set(_expected_responses[0].capitalize())
        self.expected_response2.set(_expected_responses[1].capitalize())

        # Update the table
        self.tree.delete(*self.tree.get_children()) # Wipe tree state
        _addressParser = AddressParser(self.globals.recipients)
        emails = _addressParser.recipients
        for email in emails:
            processed = email in self.globals.responses
            processed = "Yes" if processed else "No"
            self.tree.insert("", tk.END, values=[email, processed])
    
    def handleDoubleClick(self, event):
        '''
        Handles doubleclick events in the treeview table and controls whether the recipient
        search screen is displayed or if no change should occur.
        '''
        
        # Get the row value that was clicked
        try:
            item = self.tree.selection()[0]
            value = self.tree.item(item,"values")
            email, processed = value
            
            # Switch to the recipient search page and pass along the row value
            "We only switch screens if value is No, since Yes indicates that a Response was found already"
            if processed == "No":
                self.switchToValidRequestRecipientSearch(self, email, self.expiry.get(), self.globals.validRequestWidget)
        except:
            "If this happens, the user clicked a blank row, shouldn't be a big deal"
            pass
    
    def show(self):
        self.pack()
    
    def hide(self):
        self.pack_forget()

class InvalidRequestWidget(BaseFrame):
    '''
    Displays details indicating an unsuccessful request validation.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        
        # FRAME ROW 1: Display failure label
        failLabel = ttk.Label(self, text="Email doesn't contain a valid Request."); failLabel.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # FRAME ROW 2: Button to go back to Request search
        self.goBackButton = ttk.Button(
            self,
            text = 'Go Back',
            width = 25,
            command = lambda: (
                self.pack_forget(),
                self.globals.responseSearchPage.pack_forget(),
                self.globals.requestResultsPage.show()
            )
        )
        self.goBackButton.pack(padx=PAD_X, pady=PAD_Y)
        
        self.globals.invalidRequestWidget = self
    
    def show(self):
        self.pack()
    
    def hide(self):
        self.pack_forget()

# ---------- Screen 2.3: Search for our responses ---------- #
class ValidRequestRecipientSearch(BaseFrame):
    '''
    Displays the details of a Request that was made.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)

        # Store component variables
        self.emailAddress = tk.StringVar(self)
        self.expiry = tk.StringVar(self)
        
        # Styling
        PAD_X=10
        PAD_Y=10
        ENTRY_WIDTH=75

        # CONTROL: Create the table to display search results
        self.searchTable = RecipientSearchResultsTable(self)
        self.searchTable.pack(padx=PAD_X, pady=PAD_Y)
        self.searchTable.pack_forget()
        
        # FRAME ROW 1: Expiry state values
        row1 = tk.Frame(self)
        expiryDescription = ttk.Label(row1, text="Expiry: "); expiryDescription.pack(side="left")
        expiryLabel = ttk.Label(row1, textvariable=self.expiry); expiryLabel.pack(side="left", padx=pad_tl(PAD_X))
        row1.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # FRAME ROW 2: Header message for search bar
        searchLabel = ttk.Label(self, text='Search for Response')
        searchLabel.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))

        # FRAME ROW 3: Search bar for finding a request email
        row3 = tk.Frame(self)
        searchBar = ttk.Entry(row3, width=ENTRY_WIDTH); searchBar.pack(side="left", padx=pad_br(PAD_X))
        searchButton = ttk.Button(row3, text="Search", command=lambda: self.search_for_responses(searchBar.get())); searchButton.pack(side="left")
        row3.pack(anchor="w", padx=PAD_X, pady=pad_tl(PAD_Y))

        # FRAME ROW 4: Button to go back to Response search
        self.goBackButton = ttk.Button(
            self,
            text = 'Go Back',
            width = 25,
            command = lambda: (
                self.hide(),
                self.globals.responseScreen.show_tally(),
                self.globals.responseSearchPage.show(),
            )
        )
        self.goBackButton.pack(padx=PAD_X, pady=PAD_Y)
        
        # FRAME ROW 5: Button to mark response as absent
        self.absentButton = ttk.Button(
            self,
            text = 'Response not received',
            command = lambda: (
                self.pack_forget(),
                self.mark_absent(self.emailAddress.get())
            )
        )
        self.absentButton.pack(padx = PAD_X, pady = PAD_Y)
        
        self.globals.validRequestRecipientSearch = self
    
    def update(self, emailAddress, expiry):
        '''
        Make this component aware of the email address of the Leader so we can
        filter results to only show ones sent from them.
        '''
        self.emailAddress.set(emailAddress)
        self.expiry.set(expiry)

    def search_for_responses(self, query):
        # Prevent dumb requests
        "It's not dumb if I/someone does it, it's just dumb because it may take a long time to resolve"
        if len(query) < 5:
            return
        
        # Perform the query
        apiClient = GmailAPI(self.globals.CREDENTIALS_DIR)
        _searchResult = apiClient.search(query)

        # Filter results
        searchResult = []
        for r in _searchResult:
            subject, sender, date, emailID, recipients = r
            _addressParser = AddressParser(sender)
            emailAddress = _addressParser.recipients[0]
            assert emailAddress != None # Error checker for debugging, this shouldn't make it live

            if emailAddress.lower() != self.emailAddress.get():
                continue
            else:
                # Expiry date modification: don't list results past the expiry time
                _sendDate = datetime.datetime.strptime(date, "%c %z")
                _expiryDate = datetime.datetime.strptime(self.expiry.get(), "%c %z")
                
                if _sendDate < _expiryDate:
                    searchResult.append(r)
        
        # Pass results to our search display table and trigger its display
        PAD_X = 10
        PAD_Y = 10
        self.globals.recipientSearchResultsTable.update(searchResult)
        self.globals.recipientSearchResultsTable.pack(padx=PAD_X, pady=PAD_Y)
    
    def mark_absent(self, sender):
        # Store a null response in our global object
        self.globals.responses[sender] = None

        # Update the responses table
        self.globals.validRequestWidget.update()

        # Check to see how many responses we have
        totalRecipients = self.globals.recipients.count("@") # This should give the number of recipients
        obtainedRecipients = len(self.globals.responses)

        # If we need to find more responses...
        if obtainedRecipients < totalRecipients:
            # Switch back to response search search without messing with state
            self.hide()
            self.globals.responseScreen.show_tally()
            self.globals.responseSearchPage.show()
        # If we've found all responses...
        else:
            # Hide existing elements
            self.globals.responseScreen.hide() # This will cascade down..?
            
            # Switch to our bundling page
            self.globals.root.show_create_bundle()
            self.globals.createBundleScreen.update()
    
    def show(self):
        self.pack()
        self.searchTable.hide()
    
    def hide(self):
        self.pack_forget(),
        self.searchTable.hide()

class RecipientSearchResultsTable(BaseFrame):
    '''
    Displays the results of Google API search as a table. Table rows can
    be double clicked to launch the handleDoubleClick() function which
    knows the row's contents that was clicked.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)

        # Component state
        self.requestID = None
        
        # Styling
        TOTAL_WIDTH=520

        # FRAME ROW(?) 1: Format the table
        self.tree = ttk.Treeview(self, column=("Subject", "From", "Date"), show='headings')
        
        self.tree.column("#1", anchor=tk.CENTER, width=int((TOTAL_WIDTH*0.4)))
        self.tree.heading("#1", text="Subject")

        self.tree.column("#2", anchor=tk.CENTER, width=int((TOTAL_WIDTH*0.4)))
        self.tree.heading("#2", text="From")

        self.tree.column("#3", anchor=tk.CENTER, width=int((TOTAL_WIDTH*0.2)))
        self.tree.heading("#3", text="Date")

        self.tree.pack()
        self.tree.bind("<Double-1>", self.handleDoubleClick)
        
        # FRAME ROW 2: Display failure messages
        self.failMessage = tk.StringVar(self)
        self.failLabel = ttk.Label(self, textvariable=self.failMessage)
        
        self.globals.recipientSearchResultsTable = self
    
    def update(self, searchResult):
        '''
        Update the table's contents with search results.
        This will reset the table on search so results don't
        accumulate over sequential searches.
        
        Arguments:
            searchResult -- A list containing at least three items with the format:
                            [subjectString, senderSTring, dateString]. An additional
                            fourth value should usually exist (but won't be shown) which
                            is the email's ID.
        
        Credit to https://www.activestate.com/resources/quick-reads/how-to-display-data-in-a-table-using-tkinter/
        '''
        self.tree.delete(*self.tree.get_children()) # Wipe tree state
        
        for r in searchResult:
            self.tree.insert("", tk.END, values=r) # Populate tree with new results
    
    def handleDoubleClick(self, event):
        '''
        When double clicking on an email that may contain a Response, this function will
        receive the row's contents and perform an API query to Gmail. The email's contents
        will be used to create a Response and, if it's validated, we'll update the table
        that lists the recipients of the original Request and store the response in a
        global variable.
        
        Once we've found all the Responses, this function will trigger the display of
        the window to show the Bundle and allow it to be copy pasted into an email.
        
        Credit to https://stackoverflow.com/questions/3794268/command-for-clicking-on-the-items-of-a-tkinter-treeview-widget
        '''
        PAD_X = 10
        PAD_Y = 10
        
        # Get the row value that was clicked
        try:
            item = self.tree.selection()[0]
            responseValue = self.tree.item(item,"values")
            subject, sender, date, emailID, recipients = responseValue
            _addressParser = AddressParser(sender)
            sender = _addressParser.recipients[0]
            assert sender != None # Error checker for debugging, this shouldn't make it live

            # Obtain the email message
            apiClient = GmailAPI(self.globals.CREDENTIALS_DIR)
            emailText = apiClient.read(emailID)
            
            # Parse it as a Response object
            response = Response(emailText)
            
            # If a valid Response was made...
            if response.isValid:
                # Check that it's for the Request
                if response.requestID == self.globals.request.id:
                    # Hide any existing error messages
                    self.failLabel.pack_forget()
                    
                    # Store it into our global state
                    self.globals.responses[sender] = response

                    # Update the responses table
                    self.globals.validRequestWidget.update()

                    # Check to see how many responses we have
                    totalRecipients = self.globals.recipients.count("@") # This should give the number of recipients
                    obtainedRecipients = len(self.globals.responses)

                    # If we need to find more responses...
                    if obtainedRecipients < totalRecipients:
                        # Switch back to response search search without messing with state
                        self.hide()
                        self.globals.responseScreen.show_tally()
                        self.globals.responseSearchPage.show()
                    # If we've found all responses...
                    else:
                        # Hide existing elements
                        self.globals.responseScreen.hide() # This will cascade down..?
                        
                        # Switch to our bundling page
                        self.globals.root.show_create_bundle()
                        self.globals.createBundleScreen.update()
                # Display message of invalidity
                else:
                    self.failMessage.set("Email contains a Response for a different Request.")
                    self.failLabel.pack()

            # Otherwise, bring up the fail message
            else:
                self.failMessage.set("Email doesn't contain a valid Response.")
                self.failLabel.pack()
        except:
            "If this happens, the user clicked a blank row, shouldn't be a big deal"
            pass
    
    def show(self):
        PAD_X = 10
        PAD_Y = 10
        self.pack(padx=PAD_X, pady=PAD_Y)
    
    def hide(self):
        self.pack_forget()

# ---------- Screen 3: Bundle creation ---------- #
class CreateBundleScreen(BaseFrame):
    '''
    This screen controls the display and copying of a Bundle
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        self.pack()
        self.globals.createBundleScreen = self
        
        # Styling
        PAD_X=10
        PAD_Y=10
        BOX_WIDTH=60
        
        # Display actual details
        bundleLabel = ttk.LabelFrame(self, text="Bundle:")
        bundleLabel.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        
        self.bundleContents = scrolledtext.ScrolledText(bundleLabel, width=BOX_WIDTH)
        self.bundleContents.pack()
        
        # Button to copy a format to clipboard
        copyButton = ttk.Button(self, text='Copy Bundle', command=lambda: pyperclip.copy(self.bundleContents.get('1.0', tk.END)))
        copyButton.pack(padx=10, pady=10)
            
    def update(self):
        '''
        Calling this function triggers this page/widget to attempt to form a Bundle using
        the Request and Responses stored within the program's global variables.
        '''
        
        # Get our bundle
        bundle = Bundle()
        bundle.create_new(self.globals.request, self.globals.responses)
        
        # Set the text display widget contents
        "If the Bundle is invalid, it still gives us a message telling us, so we can use its string method"
        self.bundleContents.insert(1.0, bundle.format_bundle_as_string())
        self.bundleContents.configure(state ='disabled')
    
    def show(self):
        self.pack()
    
    def hide(self):
        self.pack_forget()

# ---------- Screen 4: Bundle finding and blockchain addition ---------- #
class CommitBundleScreen(BaseFrame):
    '''
    This screen controls the process of commiting a Bundle to the blockchain.
    '''
    def __init__(self, parent):
        # use the __init__ of the superclass to create the actual frame
        BaseFrame.__init__(self, parent)
        self.pack()
        
        # Styling
        PAD_X=10
        PAD_Y=10
        BOX_WIDTH=60
        
        # Display actual details
        bundleLabel = ttk.LabelFrame(self, text="Paste Bundle: "); bundleLabel.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        self.bundleText = scrolledtext.ScrolledText(bundleLabel, width=BOX_WIDTH); self.bundleText.pack()
        
        # Commit success / failure label
        self.successMessage = tk.StringVar(self)
        self.successMessage.set("Waiting on a bundle...")
        successLabel = ttk.Label(self, textvariable=self.successMessage); successLabel.pack(padx=PAD_X, pady=pad_tl(PAD_Y))
        
        # Button to commit a Bundle from clipboard
        commitButton = ttk.Button(self, text='Commit Bundle', command=lambda: self.commit()); commitButton.pack(padx=PAD_X, pady=PAD_Y)
        
        self.globals.commitBundleScreen = self
    
    def commit(self):
        '''
        Commits a valid bundle after the button is pressed.
        '''
        # Get our bundle
        bundle = Bundle()
        isValid = bundle.parse_from_email(self.bundleText.get('1.0', tk.END), self.globals.blockchain)

        # If the Bundle is invalid...
        if not isValid:
            # ... just set an alert for this
            self.successMessage.set("Bundle isn't valid!")
        # If the bundle is valid...
        else:
            # ... create a block
            block = BundleBlock(bundle, self.globals.blockchain.get_last_block().hash)
            
            # ... commit it to the blockchain
            "If this isn't added, saving the blockchain will have no effect"
            wasAdded = self.globals.blockchain.add_block(block)
            
            # ... save the blockchain
            wasSaved = self.globals.blockchain.save()
            
            # ... then give an alert to this outcome
            if wasSaved and wasAdded:
                self.successMessage.set("Bundle committed!")
            elif not wasAdded:
                self.successMessage.set("Duplicate bundle not commited")
            else:
                self.successMessage.set("Bundle not commited for an unknown reason")
    
    def show(self):
        self.pack()
    
    def hide(self):
        self.pack_forget()
