import json
from web3 import Web3
import os
import time
from decimal import Decimal
from dotenv import load_dotenv
from hashlib import sha256

def deploy_contract(abi,bytecode,url):

    web3 = Web3(Web3.HTTPProvider(url))
    
    load_dotenv()
    account_address = os.getenv("ACCOUNT_ADDRESS")
    private_key = os.getenv('PRIVATE_KEY')

    contract = web3.eth.contract(abi=abi, bytecode=bytecode)

    tx = contract.constructor().buildTransaction({'nonce': web3.eth.getTransactionCount(account_address), 'from': account_address,"gasPrice": web3.eth.gas_price})

    signed_tx = web3.eth.account.signTransaction(tx, private_key=private_key)

    tx_transact = web3.eth.sendRawTransaction(signed_tx.rawTransaction)


    tx_receipt = web3.eth.waitForTransactionReceipt(tx_transact)
    
    return tx_receipt

def create_contract(abi,url,messageID,expiry,businessRequirement,contract_address,messageSubject,messageContent,messageDate,keyID):

    web3 = Web3(Web3.HTTPProvider(url,request_kwargs={'timeout': 600}))
    contract = web3.eth.contract(
        address=contract_address,
        abi=abi,
    )
    
    load_dotenv()
    account_address = os.getenv("ACCOUNT_ADDRESS")
    private_key = os.getenv('PRIVATE_KEY')
    messageSubjectHash = sha256(messageSubject.encode('utf-8')).hexdigest()
    messageContentHash = sha256(messageContent.encode('utf-8')).hexdigest()
    keyIDHash = sha256(keyID.encode('utf-8')).hexdigest()

    tx = contract.functions.createContract(messageID,expiry,businessRequirement,messageContentHash,messageDate,keyIDHash).buildTransaction({'nonce': web3.eth.getTransactionCount(account_address), 'from': account_address,"gasPrice": web3.eth.gas_price})

    signed_tx = web3.eth.account.signTransaction(tx, private_key=private_key)

    tx_transact = web3.eth.sendRawTransaction(signed_tx.rawTransaction)


    tx_receipt = web3.eth.waitForTransactionReceipt(tx_transact)
    
    
    return tx_receipt


def register_voter(contract_address, abi, url,recipientAddress,account_address,private_key, messageID):
    

    web3 = Web3(Web3.HTTPProvider(url,request_kwargs={'timeout': 600}))
    contract = web3.eth.contract(
        address=contract_address,
        abi=abi,
    )

    
    tx = contract.functions.RegisterVoter(recipientAddress,messageID).buildTransaction({'nonce': web3.eth.getTransactionCount(account_address), 'from': account_address, "gasPrice": web3.eth.gas_price})

    signed_tx = web3.eth.account.signTransaction(tx, private_key=private_key)
    
    tx_transact = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_transact)
    return tx_receipt

def check_contract(contract_address, abi, url,keyID):
    
    web3 = Web3(Web3.HTTPProvider(url))
    contract = web3.eth.contract(
        address=contract_address,
        abi=abi,
    )
    keyIDHash = sha256(keyID.encode('utf-8')).hexdigest()
    return contract.functions.getIsCreated(keyIDHash).call()

def vote(contract_address, abi, url,account_address,private_key,responseString,messageID):
    
    web3 = Web3(Web3.HTTPProvider(url,request_kwargs={'timeout': 600}))
    contract = web3.eth.contract(
        address=contract_address,
        abi=abi,
    )


    tx = contract.functions.Vote(responseString,messageID).buildTransaction({'nonce': web3.eth.getTransactionCount(account_address), 'from': account_address, "gasPrice": web3.eth.gas_price})

    signed_tx = web3.eth.account.signTransaction(tx, private_key=private_key)

    tx_transact = web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    tx_receipt = web3.eth.waitForTransactionReceipt(tx_transact)
    return tx_receipt

def check_consistency(contract_address, abi, url,keyID,messageContent,expiryTime,businessRequirement):
    web3 = Web3(Web3.HTTPProvider(url))
    contract = web3.eth.contract(
        address=contract_address,
        abi=abi,
    )
    keyIDHash = sha256(keyID.encode('utf-8')).hexdigest()
    return contract.functions.checkConsistency(keyIDHash,businessRequirement,expiryTime,messageContent).call()
    
def getBundle(abi, url,contractAddress,private_key,account_address,messageID):

    contract_address = contractAddress
    web3 = Web3(Web3.HTTPProvider(url))
    contract = web3.eth.contract(
        address=contract_address,
        abi=abi,
    )
    isCompiled = contract.functions.getIsCompiled(messageID).call()
    if isCompiled == False:
        consensus(contract_address,abi,account_address,private_key,url,messageID)
    Bundle = compile_bundle(contract_address,abi,url,messageID)
    if Bundle[0] == True:
        Bundle[0] = "Accepted"
    else:
        Bundle[0] = "Rejected"
    stringBundle = "\nBundle:\nVerdict: {}\nVote Count: {}\nMessage ID: {}\nVoters: {}".format(Bundle[0],Bundle[2],Bundle[1].hex(),Bundle[3])
    return stringBundle
    

def consensus(contractAddress,contractABI,account_address,private_key,url,messageID):
    web3 = Web3(Web3.HTTPProvider(url))
    contract = web3.eth.contract(
        address=contractAddress,
        abi=contractABI,
    )
    tx = contract.functions.Consensus(messageID).buildTransaction({'nonce': web3.eth.getTransactionCount(account_address), 'from': account_address, "gasPrice": web3.eth.gas_price})

    signed_tx = web3.eth.account.signTransaction(tx, private_key=private_key)
    
    tx_transact = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
    tx_receipt = web3.eth.waitForTransactionReceipt(tx_transact)
    return tx_receipt

def compile_bundle(contractAddress,contractABI,url,messageID):
    web3 = Web3(Web3.HTTPProvider(url))
    contract = web3.eth.contract(
        address=contractAddress,
        abi=contractABI,
    )
    return contract.functions.retrieve_bundle(messageID).call()

load_dotenv()
bytecode = os.getenv('BYTECODE')
url = os.getenv('URL')
abi = os.getenv('ABI')
account_address = os.getenv('ACCOUNT_ADDRESS')
private_key = os.getenv('PRIVATE_KEY')
contract_address = os.getenv('Contract_Address')

#The Smart Contract will be deployed using the following lines of code
# tx = deploy_contract(abi,bytecode,url)
# print(tx["contractAddress"])