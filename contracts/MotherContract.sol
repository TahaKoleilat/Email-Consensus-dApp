pragma solidity >=0.7.0 <0.9.0;
import "./BusinessConsensus.sol";
contract MotherContract{
    mapping(bytes32 => address) public userContractAddress;
    mapping(bytes32 => bytes32) public businessProposals;
    function createContractInstance(address contractAddress, bytes32 _subject) external {
      BusinessConsensus smartContract = BusinessConsensus(contractAddress);
      bytes32 proposalID = keccak256(bytes(smartContract.getValues()));
      userContractAddress[proposalID] = contractAddress;
      businessProposals[_subject] = proposalID;
    }
    function getContractAddress(string memory _messageID) external view returns (address){
      bytes32 tempVar = keccak256(bytes(_messageID));
      return userContractAddress[tempVar];
    }
    function getConsistentParams(bytes32 _subject) external view returns (bool,bool,bool){
      BusinessConsensus smartContract = BusinessConsensus(userContractAddress[businessProposals[_subject]]);
      var (content, expiryDur, requirement) = smartContract.getValues()
      bool value1 = true;
        bool value2 = true;
        bool value3 = true;
        if(_businessRequirement != businessProposals[_subject].BusinessRequirement){
            value1 = false;
        }
        if(_contents != businessProposals[_subject].contents){
            value2 = false;
        }
        if(businessProposals[_subject].expiryLength != _expiryLength){
            value3 = false;
        }
    return (value1,value2,value3);
      return (businessProposals[_subject],content,proposal.expiryLength,BusinessRequirement)
    }
}