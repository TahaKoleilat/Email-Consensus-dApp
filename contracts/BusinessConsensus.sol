pragma solidity >=0.7.0 <0.9.0;
contract BusinessConsensus{
    // This declares a new complex type which will
    // be used for variables later.
    // It will represent a single voter.
    struct Voter {
        bool voted;  // if true, that person already voted
        bool vote;   //represents approval or disapproval
        address recipient; // represents a stakeholder recipient
    }

    mapping(bytes32=>address) public initiators;
    mapping(bytes32 =>bytes32) public IDs;
    mapping(bytes32 => uint256) public voteCounts;
    mapping(bytes32 => uint256) public expiryLengths;
    mapping(bytes32 => uint256) public expiryDates;
    mapping(bytes32 => bytes32) public contents;
    mapping(bytes32 => uint256) public numApprovals;
    mapping(bytes32 => uint256) public businessRequirements;
    mapping(bytes32 => string) public messageDates;
    mapping(bytes32 => bool) public finalVerdicts;
    mapping(bytes32 => bool) public isCompiled;
    mapping(bytes32=>mapping(address=>Voter)) public voter_maps;
    mapping(bytes32=>Voter[]) public Voters;
    mapping(bytes32=>address[]) public keys;
    
    function createContract(bytes32 _messageID, uint256 expiry, uint256 requiredPercentage,bytes32 _contents,
    string memory _messageDate, bytes32 _keyID) external{
        // initialize proposal set by the original sender and counted votes to zero
        require(initiators[_messageID] == address(0),"Proposal already created!");
            voteCounts[_messageID] = 0;
            expiryDates[_messageID] =  block.timestamp + expiry;
            IDs[_keyID] = _messageID;
            isCompiled[_messageID] = false;
            businessRequirements[_messageID] = requiredPercentage;
            businessRequirements[_keyID] = requiredPercentage;
            finalVerdicts[_messageID] = false;
            expiryLengths[_keyID] = expiry;
            contents[_keyID] = _contents;
            messageDates[_keyID] = _messageDate;
            numApprovals[_messageID] = 0;
            initiators[_messageID] = msg.sender;

    }
    function getIsCompiled(bytes32 _messageID) public view returns (bool){
        return isCompiled[_messageID];
    }
    function checkConsistency(bytes32 _keyID, uint256 _businessRequirement, uint256 _expiryLength, bytes32 _contents) public view returns(bool, bool, bool){
        bool value1 = true;
        bool value2 = true;
        bool value3 = true;
        if(_businessRequirement != businessRequirements[_keyID]){
            value1 = false;
        }
        if(_contents != contents[_keyID]){
            value2 = false;
        }
        if(expiryLengths[_keyID] != _expiryLength){
            value3 = false;
        }
    return (value1,value2,value3);

    }
    function getIsCreated(bytes32 _keyID) public view returns (bytes32,string memory){
        return (IDs[_keyID],messageDates[_keyID]);
    }
    // Give `voter` the right to vote in this proposal.
    // May only be called by `initiator`.
    function RegisterVoter(address voter,bytes32 _messageID) external {
        // only initiator can register a recipient in the voting process
        require(
            msg.sender == initiators[_messageID],
            "Only initiator can register a recipient."
        );
        require(voter != initiators[_messageID], "Initiator can't vote!");

        require(voter_maps[_messageID][voter].recipient == address(0), "Recipient is already registered");

        require(block.timestamp < expiryDates[_messageID], "Proposal has reached its expiry date");

        Voter memory x = Voter({voted: false,recipient: voter, vote: false});
        voter_maps[_messageID][voter] = x;
        keys[_messageID].push(voter);
    }

    function Vote(string memory response,bytes32 _messageID) external {

        require(block.timestamp < expiryDates[_messageID], "Voting has expired");
        require(voter_maps[_messageID][msg.sender].recipient != address(0x0), "You are not registered to vote");
        require(!voter_maps[_messageID][msg.sender].voted, "You already sent a response.");

        if(keccak256(bytes(response)) == keccak256(bytes("i approve"))){
            voter_maps[_messageID][msg.sender].voted = true;
            voter_maps[_messageID][msg.sender].vote = true;
            numApprovals[_messageID] += 1;
            voteCounts[_messageID] += 1;
            Voters[_messageID].push(voter_maps[_messageID][msg.sender]);
        }

        else if(keccak256(bytes(response)) == keccak256(bytes("i disapprove"))){
            voter_maps[_messageID][msg.sender].voted = true;
            voteCounts[_messageID] += 1;
            Voters[_messageID].push(voter_maps[_messageID][msg.sender]);
        }
        //if given invalid response, it will be considered a disapproval
        else{
            voter_maps[_messageID][msg.sender].voted = true;
            voteCounts[_messageID] += 1;
            Voters[_messageID].push(voter_maps[_messageID][msg.sender]);
        }
        
    }

    /// compile all relevant information into a Bundle
    function Consensus(bytes32 _messageID) external {
        require(block.timestamp >= expiryDates[_messageID], "Verdict has not been reached yet");
        require(isCompiled[_messageID] == false, "Consensus has already been calculated");
        require(msg.sender == initiators[_messageID] || voter_maps[_messageID][msg.sender].recipient != address(0x0),
         "You aren't authorize to compile Bundle");
        uint256 AccumulatedPercentage = (numApprovals[_messageID]/keys[_messageID].length)*100;
        if(AccumulatedPercentage >= businessRequirements[_messageID]){
            finalVerdicts[_messageID] = true;
        }
        for(uint8 i=0; i< keys[_messageID].length; i++){
            if(voter_maps[_messageID][keys[_messageID][i]].voted == false){
                Voters[_messageID].push(voter_maps[_messageID][keys[_messageID][i]]);
            }
        }
        isCompiled[_messageID] = true;
    }

    function retrieve_bundle(bytes32 _messageID) external view returns (bool, bytes32, uint256, Voter[] memory){
        require(block.timestamp >= expiryDates[_messageID], "Verdict has not been reached yet");
        Voter[] memory voters = Voters[_messageID];
        bool verdict = finalVerdicts[_messageID];
        uint256 count = voteCounts[_messageID];
        return (verdict,_messageID,count,voters);
        
    }

}