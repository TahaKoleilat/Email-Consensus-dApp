#! python3
# message.py
# Provides request and response objects for the P.O.C application.

import time, datetime
import re, json, unittest
from hashlib import sha256

# ---------- Global values ---------- #
BYZANTINE_RATIO = 0.8

ACTION_TYPES = ["approval"]
DERIVE_ACTION_TYPES_FROM_EXPECTED = {
    "['i approve', 'i disapprove']": "approval"
}

EXPIRY_REGEX = re.compile("^\d{1,3}[dhm]$")

messageFormat = '''\
# ---------- START BLOCKCHAIN REQUEST ---------- #
# MESSAGE DATE: {0}
# EXPIRY DATE: {1}
# MESSAGE ID: {2}
# MESSAGE CONTENTS: {3}
# ACTION REQUESTED: {4}
# ---------- END BLOCKCHAIN REQUEST ---------- #
'''

actionFormat = '''\
Please reply with a copy of the "BLOCKCHAIN RESPONSE" below.
# Edit the MESSAGE RESPONSE field to say "I {0}" if YES, or "I {1}" if NO to the proposal.\
'''

responseFormat = '''\
# ---------- START BLOCKCHAIN RESPONSE ---------- #
# MESSAGE ID: {0}
# MESSAGE RESPONSE: I {1} OR I {2}
# ---------- END BLOCKCHAIN RESPONSE ---------- #
'''

bundleFormat = '''\
# ---------- START BLOCKCHAIN BUNDLE ---------- #
# REQUEST ID: {0}
# REQUEST CONTENTS: {1}
# ACTION REQUESTED: {2}
# RECIPIENTS: {3}
# RESPONSES: {4}
# VERDICT: {5}
# ---------- END BLOCKCHAIN BUNDLE ---------- #
'''

# ---------- Unit tests ---------- #
class TestBundle(unittest.TestCase):
    def test_bundle_can_form(self):
        # Arrange
        req = Request()
        req.create_new("Test", "approval")
        
        email_string = '''\
# ---------- START BLOCKCHAIN RESPONSE ---------- #
# MESSAGE ID: {0}
# MESSAGE RESPONSE: I approve
# ---------- END BLOCKCHAIN RESPONSE ---------- #
'''.format(req.id)
        res1 = Response(email_string)
        res2 = Response(email_string)
        res3 = Response(email_string)
        res4 = Response(email_string)
        res5 = Response(email_string)
        
        responses = [res1, res2, res3, res4, res5]
        recipients = ["a@a.com", "b@b.com", "c@c.com", "d@d.com", "e@e.com"]
        responseDict = {}
        for i in range(len(responses)):
            responseDict[recipients[i]] = responses[i]

        # Act
        bundle = Bundle()
        bundle.create_new(req, responseDict)
        
        # Assert
        self.assertTrue(bundle.verdict)
    
    def test_bundle_errors_gracefully(self):
        # Arrange
        req = Request()
        req.create_new("Test", "approval")
        
        email_string = '''\
# ---------- START BLOCKCHAIN RESPONSE ---------- #
# MESSAGE ID: totesNotTheID
# MESSAGE RESPONSE: I approve
# ---------- END BLOCKCHAIN RESPONSE ---------- #
'''.format(req.id)
        res1 = Response(email_string)
        res2 = Response(email_string)
        res3 = Response(email_string)
        res4 = Response(email_string)
        res5 = Response(email_string)
        
        responses = [res1, res2, res3, res4, res5]
        recipients = ["a@a.com", "b@b.com", "c@c.com", "d@d.com", "e@e.com"]
        responseDict = {}
        for i in range(len(responses)):
            responseDict[recipients[i]] = responses[i]
        
        # Act
        bundle = Bundle()
        bundle.create_new(req, responseDict)
        
        # Assert
        self.assertTrue(bundle.verdict)

# ---------- Object class definition ---------- #
class Bundle:
    '''
    Bundle instances represent a Leader's efforts of creating a Request,
    waiting for Responses, then locating them all and bundling their Responses
    together. A Bundle is intended to be human readable, but also to be used
    as the basis for a block in the blockchain to permanently store the Request's
    outcome.
    '''
    def __init__(self):
        self.request = None
        self.responseDict = None
        self.recipients = None
        self.responses = None
        self.verdict = None
    
    def create_new(self, request, responseDict):
        '''
        Turn this into a new Bundle instance by providing the Request that
        forms the basis of the Bundle, and the responses obtained from each
        recipient.
        
        Arguments:
            request -- The Request object that this Bundle is based on.
            responseDict -- A dictionary containing keys of recipient
                            email addresses, and values of their Response
                            parsed from their email messages.
        '''
        # Validate types
        assert type(responseDict).__name__ == "dict"
        
        self.request = request
        self.responseDict = responseDict
        self.recipients = list(responseDict.keys())
        self.responses = list(responseDict.values())
                    
        # Validate the bundle
        try:
            '''
            This code is being updated to allow None Responses. The reason is to allow Responses to be
            marked as "absent" which corresponds to a Response of None.
            '''
            assert all([response == None or response.requestID == request.id for response in self.responses])
            self.verdict = self.make_verdict()
        except:
            self.verdict = None # not needed, but just shown for emphasis
    
    def parse_from_email(self, email_string, localBlockchainObj):
        '''
        This function parses an email's contents to see if it can extract a
        valid Bundle from it. If it can, this object will be updated with
        the details of the Bundle and the function will return True. Otherwise,
        this object remains in its previous state and the function returns False.
        
        Arguments:
            email_string -- The contents of an email as text.
            localBlockchainObj -- The LocalBlockchain instance containing data blocks.
        '''
        email_string = email_string.replace("\r", "")
        
        # Pull out the block of text corresponding to our bundle
        "We're being VERY careful here because emails can have newlines ANYWHERE and it's ANNOYING"
        bundleRegex = re.compile(
            r"#.+?-{10}.+?START.+?BLOCKCHAIN.+?BUNDLE.+?-{10}.+?#\n(.+?)\n#..?-{10}.+?END.+?BLOCKCHAIN.+?BUNDLE.+?-{10}.+?#\n"
        , re.DOTALL)
        bundleBlock = bundleRegex.search(email_string)
        if bundleBlock == None:
            return False
        else:
            bundleBlock = bundleBlock[1]
        
        # Parse the block to find our bundle contents
        parseRegex = re.compile(
            r"^#.+?REQUEST.+?ID:.+?(.+?)\n#.+?REQUEST.+?CONTENTS:.+?(.+?)\n#.+?ACTION.+?REQUESTED:.+?(.+?)\n#.+?RECIPIENTS:.+?(.+?)\n#.+?RESPONSES:.+?(.+?)\n.+?VERDICT:.+?(.+?)$"
        , re.DOTALL)
        parse = parseRegex.search(bundleBlock)
        if parse == None:
            return False

        id, message, action, recipients, responses, verdict = parse[1], parse[2], parse[3], parse[4], parse[5], parse[6]
        
        # Remove newlines where needed
        while "\n" in id or "  " in id:
            id = id.replace("\n", " ")
            id = id.replace("  ", " ")
        while "\n" in message or "  " in message:
            message = message.replace("\n", " ")
            message = message.replace("  ", " ")
        while "\n" in action or "  " in action:
            action = action.replace("\n", " ")
            action = action.replace("  ", " ")
        while "\n" in recipients or "  " in recipients:
            recipients = recipients.replace("\n", " ")
            recipients = recipients.replace("  ", " ")
        while "\n" in responses or "  " in responses:
            responses = responses.replace("\n", " ")
            responses = responses.replace("  ", " ")
        while "\n" in verdict or "  " in verdict:
            verdict = verdict.replace("\n", " ")
            verdict = verdict.replace("  ", " ")
        
        # Retrieve the logged RequestBlock from the blockchain
        requestBlock = localBlockchainObj.find_block_by_hash(id)
        if requestBlock == False: # i.e., if the Request is not logged
            return False # abort Bundle creation if unlogged
        
        # Validate the Bundle
        if requestBlock.requestID != id or requestBlock.message != message or requestBlock.action != action:
            return False # abort Bundle creation if logged Request doesn't match
        self.requestID = requestBlock.requestID
        self.message = requestBlock.message
        self.action = requestBlock.action
        self.date = requestBlock.date
        
        # Regenerate the Request object
        request = Request()
        request.create_new(message, action)
        request.id = requestBlock.requestID
        request.hash = requestBlock.requestID
        request.date = requestBlock.date
        self.request = request

        # Validate recipients and responses
        recipients = recipients.split(", ")
        responses = responses.split(", ")
        if len(recipients) != len(responses):
            return False # abort Bundle creation if email is not formatted correctly
        
        # Create Response objects (mocked-up)
        "We're not making a real Request. It's a problem for another time... (sorry!)"
        _responses = []
        for i in range(len(responses)):
            r = Response("")
            r.requestID = id
            r.responseContents = responses[i]
            r.isValid = True
            _responses.append(r)
        responses = _responses
        
        # Create responseDict
        responseDict = {}
        for i in range(len(recipients)):
            responseDict[recipients[i]] = responses[i]
        self.recipients = recipients
        self.responses = responses
        self.responseDict = responseDict
        
        # Get the verdict
        '''
        Implicit assumption that the bundle is correctly formatted. I 
        believe making this program immune to errors goes beyond the scope
        of the project, since I'd spend all my time just debugging the
        "helper program" rather than actually implementing a novel
        consensus process. I'm sorry if this code does get used in the
        future, I know it's getting a little spaghetti-like now.
        '''
        self.verdict = True if verdict == "ACCEPTED" else "REJECTED"
        
        return True

    def make_verdict(self):
        '''
        This function should be called alongside the Bundle creation methods
        create_new() and parse_from_email(). It tallies the Responses to 
        find the ratio of "YES" to "NO" Responses, and forms a verdict
        for whether the Request was approved or not.
        '''
        yes, no = self.request.get_expected_responses()

        # Tally the responses
        tally = []
        for response in self.responses:
            if response == None:
                tally.append(False)
            elif response.responseContents.lower() == yes:
                tally.append(True)
            elif response.responseContents.lower() == no:
                tally.append(False)
            else:
                raise Exception("Unknown response type when making verdict")
        
        # Figure out if it meets our Byzantine tolerance cutoff
        yesCount = sum(tally)
        yesRatio = yesCount / len(tally)

        # If it does, draw a True ("YES") verdict
        if yesRatio >= BYZANTINE_RATIO:
            return True
        # Otherwise, the Request has failed, so return a False ("NO") verdict
        else:
            return False
    
    def format_bundle_as_string(self):
        '''
        Generate a string representation of a Bundle which can be pasted into
        an email message.
        '''
        
        if self.verdict != None:
            message = bundleFormat.format(
                self.request.id,
                self.request.message,
                self.request.action,
                ", ".join(self.recipients),
                ", ".join(["No response" if r == None else r.responseContents for r in self.responses]),
                "ACCEPTED" if self.verdict else "REJECTED"
            )
        else:
            message = "Bundle is invalid; no verdict achieved."
        
        return message

    def format_bundle_as_json(self):
        '''
        Generate a JSON representation of a Bundle that can be used to
        form a block in the blockchain.
        '''
        
        bundleJSON = {
            "request": self.request.format_request_as_json(),
            "responses": json.dumps(
                [{ email: response.format_response_as_json() } for email, response in self.responseDict.items()]
            )
        }
        
        return json.dumps(bundleJSON)

class Request:
    '''
    Request instances represent a leader's proposed Request. This class primarily
    assists in formatting a valid message to send in an email to recipients.
    '''
    def __init__(self, expiryLength="12h",alreadySent=False,inputtedTime=''):
        assert EXPIRY_REGEX.match(expiryLength) != None
        
        self.expiryLength = expiryLength
        self.id = None
        self.message = None
        self.action = None
        self._compute_times(alreadySent,inputtedTime)
    
    def _compute_times(self,alreadySent,inputtedTime):
        # Get timezone
        timezoneOffsetInSeconds = time.localtime().tm_gmtoff
        timezoneOffsetInHours = timezoneOffsetInSeconds / 60 / 60
        timezoneOffset = str(abs(timezoneOffsetInHours)).replace(".", "").ljust(4, "0")
        timezoneOffset = "+{0}".format(timezoneOffset) if timezoneOffsetInHours >= 0 else "-{0}".format(timezoneOffset)
        if(alreadySent==False):
            # Get the current time and date
            currentTimeStamp = time.time()
            currentTime = datetime.datetime.fromtimestamp(currentTimeStamp)
            date = datetime.datetime.ctime(currentTime).replace("  ", " ")
            
            # Get the time from now + expiry length
            if "d" in self.expiryLength:
                delta = datetime.timedelta(days = int(self.expiryLength[:-1]))
            elif "h" in self.expiryLength:
                delta = datetime.timedelta(hours = int(self.expiryLength[:-1]))
            else:
                delta = datetime.timedelta(minutes = int(self.expiryLength[:-1]))

            expiry = datetime.datetime.ctime(currentTime + delta).replace("  ", " ")
            date = "{0} {1}".format(date, timezoneOffset)
            expiry = "{0} {1}".format(expiry, timezoneOffset)
            # Save to instance fields
            self.date = date
            self.expiry = expiry
        elif(alreadySent == True):
            listTime = inputtedTime.split("+")
            inputtedTime  = listTime[0].rstrip()
            expiryLength = listTime[2].rstrip()
            timezone = listTime[1].rstrip()
            
            # Get the time from now + expiry length
            if "d" in expiryLength:
                delta = datetime.timedelta(days = int(expiryLength[:-1]))
            elif "h" in expiryLength:
                delta = datetime.timedelta(hours = int(expiryLength[:-1]))
            else:
                delta = datetime.timedelta(minutes = int(expiryLength[:-1]))
            # Add timezone offsets

            datetime_inputtedTime = datetime.datetime.strptime(inputtedTime, '%a %b %d %H:%M:%S %Y')
            expiry = datetime.datetime.ctime(datetime_inputtedTime + delta).replace("  ", " ")
            date = "{0} +{1}".format(inputtedTime, timezone)
            expiry = "{0} +{1}".format(expiry, timezone)
            self.date = date
            self.expiry = expiry
    
    def create_new(self, messageContents, action):
        '''
        Turn this into a new Request instance by providing the message contents which will
        be our "request", and the action that is required in response.
        
        Arguments:
            messageContents -- The specifically worded request to be made of recipients.
                               This is a string in plain human language that should have an obvious
                               meaning for any recipients.
            action -- A string indicating the type of Request being made. Currently, this
                      class supports values including:
        '''
        try:
            assert action in ACTION_TYPES
        except:
            print("{0} not supported".format(action))
        
        # Remove newlines from messageContents
        "We can't support newlines with the regex-based parsing that we have"
        messageContents = messageContents.replace("\r", "").replace("\n", " ").strip(" ")
        
        # Hash the message contents and date to serve as our message ID
        messageHash = self.get_message_hash(messageContents, self.date)
        
        # Store values as object attributes
        self.id = messageHash
        self.message = messageContents
        self.action = action
    
    def parse_from_email(self, email_string):
        '''
        This function parses an email's contents to see if it can extract a
        valid Request from it. If it can, this object will be updated with
        the details of the Request and the function will return True. Otherwise,
        this object remains in its previous state and the function returns False.
        
        Arguments:
            email_string -- The contents of an email as text.
        '''
        email_string = email_string.replace("\r", "")

        # Pull out the block of text corresponding to our request
        "We're being VERY careful here because emails can have newlines ANYWHERE and it's ANNOYING"
        requestRegex = re.compile(
            r"#.+?-{10}.+?START.+?BLOCKCHAIN.+?REQUEST.+?-{10}.+?#\n(.+?)\n#..?-{10}.+?END.+?BLOCKCHAIN.+?REQUEST.+?-{10}.+?#\n"
        , re.DOTALL)
        requestBlock = requestRegex.search(email_string)
        if requestBlock == None:
            return False
        else:
            requestBlock = requestBlock[1]
        
        # Parse the block to find our message contents
        parseRegex = re.compile(
            r"^#.+?MESSAGE.DATE:.+?(.+?)\n#.+?EXPIRY.+?DATE:.+?(.+?)\n#.+?MESSAGE.+?ID:.+?(.+?)\n#.+?MESSAGE.+?CONTENTS:.+?(.+?)\n#.+?ACTION.+?REQUESTED:.+?\n#.+?Edit.+?the.+?MESSAGE.+?RESPONSE.+?field.+?to.+?say.+?\"(I.+?[A-Za-z]+?)\".+?if.+?YES,.+?or.+?\"(I.+?[A-Za-z]+?)\".+?if.+?NO"
        , re.DOTALL)
        parse = parseRegex.search(requestBlock)
        if parse == None:
            return False

        date, expiry, id, message, expectedYes, expectedNo = parse[1], parse[2], parse[3], parse[4], parse[5].lower(), parse[6].lower() # Make case insensitive
        
        # Remove newlines where needed
        while "\n" in date or "  " in date:
            date = date.replace("\n", " ")
            date = date.replace("  ", " ")
        while "\n" in expiry or "  " in expiry:
            date = date.replace("\n", " ")
            date = date.replace("  ", " ")
        while "\n" in id or "  " in id:
            id = id.replace("\n", " ")
            id = id.replace("  ", " ")
        while "\n" in message or "  " in message:
            message = message.replace("\n", " ")
            message = message.replace("  ", " ")
        while "\n" in expectedYes or "  " in expectedYes:
            expectedYes = expectedYes.replace("\n", " ")
            expectedYes = expectedYes.replace("  ", " ")
        while "\n" in expectedNo or "  " in expectedNo:
            expectedNo = expectedNo.replace("\n", " ")
            expectedNo = expectedNo.replace("  ", " ")
        
        # Validate the hash
        _id = self.get_message_hash(message, date)
        if _id != id:
            return False
        
        # Derive our requested action
        try:
            action = DERIVE_ACTION_TYPES_FROM_EXPECTED[str([expectedYes, expectedNo])]
        except:
            return False
        
        # Store values as object attributes
        self.date = date
        self.expiry = expiry
        self.id = id
        self.message = message
        self.action = action
        
        return True
    
    def get_message_hash(self, messageContents, date):
        '''
        Using a message's contents i.e., just the string part of the message (not
        the "# MESSAGE CONTENTS: " part) and the date, derive the hash of this Request.
        This function serves both as a way to make a Request, as well as a way to validate
        a Request.
        '''
        jsonToHash = json.dumps({
            "messageContents": messageContents,
            "date": date
        }, sort_keys=True)
        return sha256(jsonToHash.encode()).hexdigest()

    def format_request_as_string(self):
        '''
        Generate a string representation of a Request which can be pasted into
        an email message.
        '''
        assert self.date != None and self.id != None and self.message != None and self.action != None
        
        if self.action == "approval":
            yes, no = "approve", "disapprove"
        
        message = "{0}\n\n{1}".format(
            messageFormat.format(
                self.date,
                self.expiry,
                self.id,
                self.message, 
                actionFormat.format(yes, no)
            ),
            responseFormat.format(
                self.id, yes, no
            )
        )
        
        return message
    
    def format_request_as_json(self):
        '''
        Generate a JSON representation of a Request which can be used to form
        a block in the blockchain.
        '''
        requestJSON = {
            # "date": self.date, # We can't use this for Bundle since the date is lost... might need a fix?
            "id": self.id,
            "message": self.message,
            "action": self.action
        }
        return json.dumps(requestJSON)
    
    def get_expected_responses(self):
        '''
        Helper function to return a list of the responses we expect for this
        Request's specified action.
        
        Return:
            expected_responses -- A list containing two elements. The first
                                  is a string indicating "YES" response for
                                  the action, and the second indicates "NO"
                                  response for the action.
        '''
        assert self.action != None
        
        for key, value in DERIVE_ACTION_TYPES_FROM_EXPECTED.items():
            if value == self.action:
                return eval(key)
        
        return None

class Response:
    '''
    Response instances represent a single recipient's response to a proposed Request.
    
    Arguments:
        email_string -- A recipients reply email as a string.
    Important attributes and methods:
        .response -- Field with "YES" if response is valid and recipient accepts the proposed
                     Request, or "NO" is response is valid and recipients denys the proposed Request.
        .request_exists, .request_is_valid -- Fields with Boolean values indicating validation success/failure.
        .response_exists, .response_is_valid -- Fields with Boolean values indicating validation success/failure.
    '''
    def __init__(self, email_string):
        self.email_string = email_string.replace("\r", "")
        self.requestID = None
        self.responseContents = None
        self.isValid = self.parse_from_email()
        
    def parse_from_email(self):
        '''
        This function parses an email's contents to see if it can extract a
        valid Response from it. If it can, this object will be updated with
        the details of the Response and the function will return True. Otherwise,
        this object remains in its previous state and the function returns False.
        '''
        
        # Pull out the block of text corresponding to our request
        responseRegex = re.compile(r"#.+?-{10}.+?START.+?BLOCKCHAIN.+?RESPONSE.+?-{10}.+?#\n# MESSAGE ID:.+?\w{64}\n#.+?MESSAGE.+?RESPONSE:.+?I.+?[A-Za-z]+?\n#.+?-{10}.+?END.+?BLOCKCHAIN RESPONSE.+?-{10}.+?#", re.DOTALL)
        responseBlock = responseRegex.search(self.email_string)
        if responseBlock == None:
            return False
        
        # Parse the block to find our message contents
        parseRegex = re.compile(r"#.+?MESSAGE.+?ID:.+?(\w{64})\s{0,10}?\n#.+?MESSAGE.+?RESPONSE:.+?(I.+?[A-Za-z]+).+?\s{0,10}", re.DOTALL)
        parse = parseRegex.search(responseBlock[0])
        if parse == None:
            return False
        
        # Store values as object attributes
        self.requestID = parse[1]
        self.responseContents = parse[2]
        
        return (True,self.responseContents,self.requestID)
    
    def format_response_as_json(self):
        '''
        Generate a JSON representation of a Response which can be used to form
        a block in the blockchain.
        '''
        responseJSON = {
            "requestID": self.requestID,
            "responseContents": self.responseContents
        }
        return json.dumps(responseJSON)
