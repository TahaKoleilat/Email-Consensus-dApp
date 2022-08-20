import json
from web3 import Web3
import os
import dotenv
from dotenv import load_dotenv
import smtplib
import imaplib
import time
import tkinter as tk
from hashlib import sha256
from tkinter import ttk

from tkinter import scrolledtext
from tkinter import ttk
from message import Request, Response
from smtp import send_email, log_in
from imap import read_email
from deploy import create_contract, register_voter, vote, getBundle, check_contract,check_consistency
from tkinter import *
from tkinter import messagebox


        
def CreateInterface(bgcolor):

    labelfromEmail = Label(root, text="Email Address: ", bg=bgcolor, font=('', 10, 'bold'))
    labelfromEmail.grid(row=0, column=0, pady=5, padx=5)
    
    root.entryfromEmail = Entry(root, width=50, textvariable=fromEmail)
    root.entryfromEmail.grid(row=0, column=1, pady=5, padx=5)

    labelpasswordEmail = Label(root, text="Password: ", bg=bgcolor, font=('', 10, 'bold'))
    labelpasswordEmail.grid(row=1, column=0, pady=5, padx=5)

    root.entrypasswordEmail = Entry(root, width=50, textvariable=passwordEmail, show="*")
    root.entrypasswordEmail.grid(row=1, column=1, pady=5, padx=5)

    labeltoEmail = Label(root, text="Recipient's Email: ", bg=bgcolor, font=('', 10, 'bold'))
    labeltoEmail.grid(row=2, column=0, pady=5, padx=5)

    root.entrytoEmail = Entry(root, width=50, textvariable=toEmail)
    root.entrytoEmail.grid(row=2, column=1, pady=5, padx=5)

    labeltoEmail = Label(root, text="Recipient's Public Address: ", bg=bgcolor, font=('', 10, 'bold'))
    labeltoEmail.grid(row=3, column=0, pady=5, padx=5)

    root.entrytoEmail = Entry(root, width=50, textvariable=recipientAddress)
    root.entrytoEmail.grid(row=3, column=1, pady=5, padx=5)

    labelsubjectEmail = Label(root, text="Subject: ", bg=bgcolor, font=('', 10, 'bold'))
    labelsubjectEmail.grid(row=4, column=0, pady=5, padx=5)


    root.entry_subjectEmail = Entry(root, width=50, textvariable=subjectEmail)
    root.entry_subjectEmail.grid(row=4, column=1, pady=5, padx=5)

    actionOptions = ["Approval"]
    root.action = tk.StringVar(root)
    root.action.set(actionOptions[0])
        
    expiryOptions = ["Days", "Hours", "Minutes"]
    root.expiryOpt = tk.StringVar(root)
    root.expiryOpt.set(expiryOptions[0])


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
    
    root.entryValue = tk.StringVar(root)
    root.entryValue.set("1")
    okayCommand = root.register(isOkay)

    actionLabel = Label(root, text="Action: ", bg=bgcolor, font=('', 10, 'bold'))
    actionLabel.grid(row=5, column=0, pady=5, padx=5)
    actionDropdown = ttk.OptionMenu(root, root.action, "", *actionOptions, command=lambda selection: root.action.set(selection))
    actionDropdown.grid(row=5, column=1, pady=0, padx=0)
    
    ## ROW 1.2: Expiry specification
    expiryLabel = Label(root, text="Expiry Date: ", bg=bgcolor, font=('', 10, 'bold'))
    expiryLabel.grid(row=5, column=2, pady=5, padx=5)
    expiryEntry = Entry(root, validate="all", validatecommand=(okayCommand, "%P"), textvariable = root.entryValue, width=10)
    expiryEntry.grid(row=5, column=3, pady=5, padx=5)
    expiryDropdown = ttk.OptionMenu(root, root.expiryOpt, "", *expiryOptions, command=lambda selection: root.expiryOpt.set(selection))
    expiryDropdown.grid(row=5, column=4, pady=5, padx=5)

    typeOptions = ["Request","Response"]
    root.type = tk.StringVar(root)
    root.type.set(typeOptions[0])
    typeLabel = Label(root, text="Type: ", bg=bgcolor, font=('', 10, 'bold'))
    typeLabel.grid(row=5, column=5, pady=5, padx=5)
    typeDropdown = ttk.OptionMenu(root, root.type, "", *typeOptions, command=lambda selection: root.type.set(selection))
    typeDropdown.grid(row=5, column=6, pady=0, padx=0)

    businessLabel = Label(root, text="Business Requirement: ", bg=bgcolor, font=('', 10, 'bold'))
    businessLabel.grid(row=6, column=2, pady=5, padx=5)
    businessEntry = Entry(root, validate="all", validatecommand=(okayCommand, "%P"), textvariable = businessRequirement, width=10)
    businessEntry.grid(row=6, column=3, pady=5, padx=5)

    labelbodyEmail = Label(root, text="Message: ", bg=bgcolor, font=('', 10, 'bold'))
    labelbodyEmail.grid(row=7, column=1)


    root.bodyEmail = scrolledtext.ScrolledText(labelbodyEmail, width=100, height=30)
    root.bodyEmail.grid(row=7, column=4, pady=5, padx=5)

    buttonsendEmail = Button(root, text="Send Email", command=sendEmail, width=20, bg="limegreen")
    buttonsendEmail.grid(row=8, column=2, padx=5, pady = 5)

    buttonretrieveBundle = Button(root, text="Retrieve Bundle", command=retrieveBundle, width=20, bg="yellow")
    buttonretrieveBundle.grid(row=8, column=4, padx=5, pady = 5)

    buttonreadEmail = Button(root, text="Read Email", command=readEmail, width=20, bg="blue")
    buttonreadEmail.grid(row=8, column=1, padx=5, pady = 5)

    buttonExit = Button(root, text="Exit", command=emailExit, width=20, bg="red")
    buttonExit.grid(row=8, column=0, padx=5, pady = 5)

    root.successMessage = tk.StringVar(root)



def emailExit():
    MsgBox = messagebox.askquestion('Exit Application', 'Are you sure you want to exit?')
    if MsgBox == 'yes':
        root.destroy()
        os.popen("LoginGUI.pyw")

def retrieveBundle():
    body = root.bodyEmail.get('1.0', END)
    r = Response(body)
    _, _, requestID = r.parse_from_email()
    load_dotenv()
    account_address = os.getenv("ACCOUNT_ADDRESS")
    private_key = os.getenv('PRIVATE_KEY')
    abi = os.getenv('ABI')
    Contract_address = os.getenv("Contract_Address")
    url = os.getenv('URL')
    strBundle = getBundle(abi, url,Contract_address,private_key,account_address,requestID)
    root.bodyEmail.insert(tk.INSERT, strBundle)

def readEmail():
    email = fromEmail.get()
    password = passwordEmail.get()
    recipient = toEmail.get()
    subject = subjectEmail.get()
    try:
        email_message = read_email(email,password,subject,recipient)
        root.bodyEmail.insert(tk.INSERT, email_message)
    except imaplib.IMAP4.error:
        messagebox.showerror("Error",message="Login failed.")
    except FieldException:
        messagebox.showerror("Error",message="Fields are missing.")   
        
def create_request(messageContents, action,messageHash=None,alreadySent=False,inputtedTime=''):
    # Strip out newlines
    "Newlines aren't supported by the Request class"
    messageContents = messageContents.replace("\r", "").replace("\n", " ") # Crude but it'll do for P.O.C.
    
    if len(root.entryValue.get()) == 0:
            root.successMessage.set("Expiry limit must be set!")
            return
    else:
        root.successMessage.set("")
        
    if len(messageContents) < 5 or messageContents == None:
        root.successMessage.set("Message must be set!")
        return
    else:
        root.successMessage.set("")
    
    # Format the expiry length
    if root.expiryOpt.get() == "Days":
        expiryDate = int(root.entryValue.get())*24*60*60
        expiryLength = "{0}d".format(root.entryValue.get())
    elif root.expiryOpt.get() == "Hours":
        expiryDate = int(root.entryValue.get())*60*60
        expiryLength = "{0}h".format(root.entryValue.get())
    else:
        expiryDate = int(root.entryValue.get())*60
        expiryLength = "{0}m".format(root.entryValue.get())
            
    # Create request
    request = Request(expiryLength,alreadySent,inputtedTime)
    
    request.create_new(messageContents, root.action.get().lower())
    if(messageHash != None):
        request.id = messageHash

    return (request.format_request_as_string(),request.id,request.date,expiryLength)
# Defining sendEmail() to send the email
class ExpiryException(Exception):
    def __init__(self, message):
        super().__init__(message)
class MessageException(Exception):
    def __init__(self, message):
        super().__init__(message)
class FieldException(Exception):
    def __init__(self, message):
        super().__init__(message)
class BusinessException(Exception):
    def __init__(self, message):
        super().__init__(message)
class TransactionException(Exception):
    def __init__(self, message):
        super().__init__(message)
class ExpiryConsistencyException(Exception):
    def __init__(self, message):
        super().__init__(message)
class BusinessConsistencyException(Exception):
    def __init__(self, message):
        super().__init__(message)
class BodyConsistencyException(Exception):
    def __init__(self, message):
        super().__init__(message)
def triggerException(expiryField, bodyField, emailField, passwordField, recipientField, recipientAddressField, subjectField, businessField, typeField):
    if(typeField == "Request"):
        if (expiryField == ""):
            raise ExpiryException("Expiry date must be set!")
        elif(emailField == "" or passwordField == "" or recipientField == "" or subjectField == "" or businessField == "" or recipientAddressField == ""):
            raise FieldException("Fields are missing")
        elif (bodyField == "\n"):
            raise MessageException("Message must be set!")
        elif (int(businessField) > 100 or int(businessField) < 0):
            raise BusinessException("Business Percentage is invalid")
    elif(typeField == "Response"):
        if(bodyField == ""):
            raise MessageException("Message must be set!")
def triggerConsistency(boolTuple):
    if(boolTuple[2] == False):
        raise ExpiryConsistencyException("Expiry dates don't match")
    if(boolTuple[0] == False):
        raise BusinessConsistencyException("Business Percentages don't match")
    if(boolTuple[1] == False):
        raise BodyConsistencyException("Message Contents don't match")

    

def sendEmail():

    # Fetching all the necessary parameters and storing in respective variables
    email = fromEmail.get()
    password = passwordEmail.get()
    recipient = toEmail.get()
    subject = subjectEmail.get()
    businessPercentage = businessRequirement.get()
    recipientEthAddress = recipientAddress.get()
    bodyOld = root.bodyEmail.get('1.0', END)
    load_dotenv()
    account_address = os.getenv("ACCOUNT_ADDRESS")
    private_key = os.getenv('PRIVATE_KEY')
    abi = os.getenv('ABI')
    Contract_address = os.getenv("Contract_Address")
    url = os.getenv('URL')

    try:
        server = log_in(email,password)
        triggerException(root.entryValue.get(), bodyOld,email, password, recipient,recipientEthAddress, subject, businessPercentage, root.type.get())
        if(root.type.get() == "Request"):
            if root.expiryOpt.get() == "Days":
                expiryDate = int(root.entryValue.get())*24*60*60
            elif root.expiryOpt.get() == "Hours":
                expiryDate = int(root.entryValue.get())*60*60
            else:
                expiryDate = int(root.entryValue.get())*60
            
            subjectHash = sha256(subject.encode('utf-8')).hexdigest()
            keyID = email + subject
            returnedResult = check_contract(Contract_address, abi, url,keyID)
            if(returnedResult[1]==''):
                body,messageID, requestDate,expiryLength = create_request(bodyOld,root.action.get())
                requestDate = requestDate + " +" + expiryLength
                result1 = create_contract(abi,url,messageID,expiryDate,int(businessPercentage),Contract_address,subject,bodyOld,requestDate,keyID)
                result2 = register_voter(Contract_address, abi, url,recipientEthAddress,account_address,private_key,messageID)
                send_email(email,server,recipient,subject,body)
            else:
                messageID = returnedResult[0].hex()
                messageDate = returnedResult[1]
                bodyOldHash = sha256(bodyOld.encode('utf-8')).hexdigest()
                boolTuple = check_consistency(Contract_address,abi,url,keyID,bodyOldHash,expiryDate,int(businessPercentage))
                triggerConsistency(boolTuple)
                body, _, _, _ = create_request(bodyOld,root.action.get(),messageID,True,messageDate)
                result2 = register_voter(Contract_address, abi, url,recipientEthAddress,account_address,private_key,messageID)
                send_email(email,server,recipient,subject,body)

        elif(root.type.get() == "Response"):
            r = Response(bodyOld)
            _, responseString, requestID = r.parse_from_email()
            result = vote(Contract_address, abi, url,account_address,private_key,responseString.lower(),requestID)
            send_email(email,server,recipient,subject,bodyOld)


        messagebox.showinfo("Success",message="Email sent successfully to " + str(recipient))

    except smtplib.SMTPAuthenticationError:
        messagebox.showerror("Error",message="Invalid username or password")
    except smtplib.SMTPConnectError:
        messagebox.showerror("Error",message="Connection timed out. Try again later.")
    except ExpiryException:
        messagebox.showerror("Error",message="Expiry limit must be set.")
    except MessageException:
        messagebox.showerror("Error",message="Message must be set.")
    except FieldException:
        messagebox.showerror("Error",message="Fields are missing.")
    except BusinessException:
        messagebox.showerror("Error",message="Business Percentage is invalid.")
    except TransactionException:
        messagebox.showerror("Error",message=result)
    except ExpiryConsistencyException:
        messagebox.showerror("Error",message="Expiry dates don't match")
    except BusinessConsistencyException:
        messagebox.showerror("Error",message="Business Percentages don't match")
    except BodyConsistencyException:
        messagebox.showerror("Error",message="Message Contents don't match")
        


# Creating object of tk class
root = tk.Tk()

# Generating random color
bgColor ='grey'


# Setting the title and background color
# disabling the resizing property
root.config(background = bgColor)
root.title("Email-based Consensus Protocol")
root.resizable(True,True)

# Creating tkinter variables
toEmail = StringVar(root)
fromEmail = StringVar(root)
recipientAddress = StringVar(root)
passwordEmail = StringVar(root)
subjectEmail = StringVar(root)
businessRequirement = StringVar(root)

# Calling the CreateWidgets() function with argument bgColor
CreateInterface(bgColor)

# Defining infinite loop to run application
root.mainloop()