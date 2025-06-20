import os
import random
import time
import schedule
from web3 import Web3
from eth_account import Account
from dotenv import load_dotenv
from solcx import compile_standard, install_solc

# --- Load Environment Variables ---
load_dotenv()

# --- Configuration ---
RPC_ENDPOINT = "https://evmrpc-testnet.0g.ai"
CHAIN_ID = 16601
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# --- DERIVE PUBLIC ADDRESS from Private Key ---
if not PRIVATE_KEY:
    raise ValueError("PRIVATE_KEY not found in .env file. Please set it.")
try:
    account = Account.from_key(PRIVATE_KEY)
    MY_ADDRESS = account.address
    print(f"Successfully derived address: {MY_ADDRESS}")
except Exception as e:
    raise ValueError(f"Invalid PRIVATE_KEY. Please check your .env file. Error: {e}")


# --- NAME GENERATION LISTS ---
ADJECTIVES = [
    "Bahlil", "Jokowi", "Prabowo", "SPBU", "Icikiwir", "Forgotten", "Glimmering",
    "Storm", "Iron", "Ethereal", "Whispering", "Ancient", "Cursed", "Crimson",
    "Void", "Astral", "Frozen", "Living", "Fallen", "Sacred", "Corrupted"
]
NOUNS = [
    "Hunter", "Dragon", "Relic", "Guardian", "Shard", "Knight", "Orb", "Crown",
    "Sentinel", "Voyager", "Golem", "Wisp", "Key", "Idol", "Spire", "Behemoth",
    "Gate", "Rune", "Soul", "Echo", "Star"
]


# ==============================================================================
# --- SOLIDITY CODE SECTION ---
# ==============================================================================

SOLIDITY_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
contract MyNFT is ERC721, Ownable {
    uint256 private _nextTokenId;
    constructor(string memory name, string memory symbol) ERC721(name, symbol) {}
    function safeMint(address to) public onlyOwner {
        uint256 tokenId = _nextTokenId++;
        _safeMint(to, tokenId);
    }
}
"""
CONTEXT_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
abstract contract Context {
    function _msgSender() internal view virtual returns (address) { return msg.sender; }
    function _msgData() internal view virtual returns (bytes calldata) { return msg.data; }
}
"""
OWNABLE_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/utils/Context.sol";
abstract contract Ownable is Context {
    address private _owner;
    event OwnershipTransferred(address indexed previousOwner, address indexed newOwner);
    constructor() { _setOwner(_msgSender()); }
    function owner() public view virtual returns (address) { return _owner; }
    modifier onlyOwner() { require(owner() == _msgSender(), "Ownable: caller is not the owner"); _; }
    function renounceOwnership() public virtual onlyOwner { _setOwner(address(0)); }
    function transferOwnership(address newOwner) public virtual onlyOwner { require(newOwner != address(0), "Ownable: new owner is the zero address"); _setOwner(newOwner); }
    function _setOwner(address newOwner) internal { address oldOwner = _owner; _owner = newOwner; emit OwnershipTransferred(oldOwner, newOwner); }
}
"""
IERC165_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
interface IERC165 {
    function supportsInterface(bytes4 interfaceId) external view returns (bool);
}
"""
ERC165_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/utils/introspection/IERC165.sol";
abstract contract ERC165 is IERC165 {
    function supportsInterface(bytes4 interfaceId) public view virtual override returns (bool) {
        return interfaceId == type(IERC165).interfaceId;
    }
}
"""
IERC721_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/utils/introspection/IERC165.sol";
interface IERC721 is IERC165 {
    event Transfer(address indexed from, address indexed to, uint256 indexed tokenId);
    event Approval(address indexed owner, address indexed approved, uint256 indexed tokenId);
    event ApprovalForAll(address indexed owner, address indexed operator, bool approved);
    function balanceOf(address owner) external view returns (uint256 balance);
    function ownerOf(uint256 tokenId) external view returns (address owner);
    function safeTransferFrom(address from, address to, uint256 tokenId) external;
    function transferFrom(address from, address to, uint256 tokenId) external;
    function approve(address to, uint256 tokenId) external;
    function getApproved(uint256 tokenId) external view returns (address operator);
    function setApprovalForAll(address operator, bool _approved) external;
    function isApprovedForAll(address owner, address operator) external view returns (bool);
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes calldata data) external;
}
"""
IERC721_RECEIVER_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
interface IERC721Receiver {
    function onERC721Received(address operator, address from, uint256 tokenId, bytes calldata data) external returns (bytes4);
}
"""
IERC721_METADATA_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
interface IERC721Metadata is IERC721 {
    function name() external view returns (string memory);
    function symbol() external view returns (string memory);
    function tokenURI(uint256 tokenId) external view returns (string memory);
}
"""
ADDRESS_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
library Address {
    function isContract(address account) internal view returns (bool) { return account.code.length > 0; }
    function sendValue(address payable recipient, uint256 amount) internal {
        require(address(this).balance >= amount, "Address: insufficient balance");
        (bool success, ) = recipient.call{value: amount}("");
        require(success, "Address: unable to send value, recipient may have reverted");
    }
    function functionCall(address target, bytes memory data) internal returns (bytes memory) { return functionCall(target, data, "Address: low-level call failed"); }
    function functionCall(address target, bytes memory data, string memory errorMessage) internal returns (bytes memory) { return functionCallWithValue(target, data, 0, errorMessage); }
    function functionCallWithValue(address target, bytes memory data, uint256 value) internal returns (bytes memory) { return functionCallWithValue(target, data, value, "Address: low-level call with value failed"); }
    function functionCallWithValue(address target, bytes memory data, uint256 value, string memory errorMessage) internal returns (bytes memory) {
        require(address(this).balance >= value, "Address: insufficient balance for call");
        require(isContract(target), "Address: call to non-contract");
        (bool success, bytes memory returndata) = target.call{value: value}(data);
        return verifyCallResult(success, returndata, errorMessage);
    }
    function functionStaticCall(address target, bytes memory data) internal view returns (bytes memory) { return functionStaticCall(target, data, "Address: low-level static call failed"); }
    function functionStaticCall(address target, bytes memory data, string memory errorMessage) internal view returns (bytes memory) {
        require(isContract(target), "Address: static call to non-contract");
        (bool success, bytes memory returndata) = target.staticcall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }
    function functionDelegateCall(address target, bytes memory data) internal returns (bytes memory) { return functionDelegateCall(target, data, "Address: low-level delegate call failed"); }
    function functionDelegateCall(address target, bytes memory data, string memory errorMessage) internal returns (bytes memory) {
        require(isContract(target), "Address: delegate call to non-contract");
        (bool success, bytes memory returndata) = target.delegatecall(data);
        return verifyCallResult(success, returndata, errorMessage);
    }
    function verifyCallResult(bool success, bytes memory returndata, string memory errorMessage) internal pure returns (bytes memory) {
        if (success) { return returndata; } else { if (returndata.length > 0) { assembly { let returndata_size := mload(returndata) revert(add(32, returndata), returndata_size) } } else { revert(errorMessage); } }
    }
}
"""
STRINGS_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
library Strings {
    bytes16 private constant _HEX_SYMBOLS = "0123456789abcdef";
    function toString(uint256 value) internal pure returns (string memory) {
        if (value == 0) { return "0"; }
        uint256 temp = value;
        uint256 digits;
        while (temp != 0) { digits++; temp /= 10; }
        bytes memory buffer = new bytes(digits);
        while (value != 0) { digits -= 1; buffer[digits] = bytes1(uint8(48 + uint256(value % 10))); value /= 10; }
        return string(buffer);
    }
    function toHexString(uint256 value) internal pure returns (string memory) {
        if (value == 0) { return "0x00"; }
        uint256 length = 0;
        uint256 temp = value;
        while (temp != 0) { length++; temp >>= 8; }
        return toHexString(value, length);
    }
    function toHexString(uint256 value, uint256 length) internal pure returns (string memory) {
        bytes memory buffer = new bytes(2 * length + 2);
        buffer[0] = "0";
        buffer[1] = "x";
        for (uint256 i = 2 * length + 1; i > 1; --i) { buffer[i] = _HEX_SYMBOLS[value & 0xf]; value >>= 4; }
        return string(buffer);
    }
}
"""
ERC721_SOURCE_CODE = """
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;
import "@openzeppelin/contracts/utils/Context.sol";
import "@openzeppelin/contracts/utils/Address.sol";
import "@openzeppelin/contracts/utils/Strings.sol";
import "@openzeppelin/contracts/utils/introspection/ERC165.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721Metadata.sol";
import "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol";
contract ERC721 is Context, ERC165, IERC721, IERC721Metadata {
    using Address for address;
    using Strings for uint256;
    string private _name;
    string private _symbol;
    mapping(uint256 => address) private _owners;
    mapping(address => uint256) private _balances;
    mapping(uint256 => address) private _tokenApprovals;
    mapping(address => mapping(address => bool)) private _operatorApprovals;
    constructor(string memory name_, string memory symbol_) {
        _name = name_;
        _symbol = symbol_;
    }
    function supportsInterface(bytes4 interfaceId) public view virtual override(ERC165, IERC165) returns (bool) {
        return
            interfaceId == type(IERC721).interfaceId ||
            interfaceId == type(IERC721Metadata).interfaceId ||
            super.supportsInterface(interfaceId);
    }
    function balanceOf(address owner) public view virtual override returns (uint256) {
        require(owner != address(0), "ERC721: balance query for the zero address");
        return _balances[owner];
    }
    function ownerOf(uint256 tokenId) public view virtual override returns (address) {
        address owner = _owners[tokenId];
        require(owner != address(0), "ERC721: owner query for nonexistent token");
        return owner;
    }
    function name() public view virtual override returns (string memory) { return _name; }
    function symbol() public view virtual override returns (string memory) { return _symbol; }
    function tokenURI(uint256 tokenId) public view virtual override returns (string memory) {
        require(_exists(tokenId), "ERC721Metadata: URI query for nonexistent token");
        string memory baseURI = _baseURI();
        return bytes(baseURI).length > 0 ? string(abi.encodePacked(baseURI, tokenId.toString())) : "";
    }
    function _baseURI() internal view virtual returns (string memory) { return ""; }
    function approve(address to, uint256 tokenId) public virtual override {
        address owner = ERC721.ownerOf(tokenId);
        require(to != owner, "ERC721: approval to current owner");
        require(_msgSender() == owner || isApprovedForAll(owner, _msgSender()), "ERC721: approve caller is not owner nor approved for all");
        _approve(to, tokenId);
    }
    function getApproved(uint256 tokenId) public view virtual override returns (address) {
        require(_exists(tokenId), "ERC721: approved query for nonexistent token");
        return _tokenApprovals[tokenId];
    }
    function setApprovalForAll(address operator, bool approved) public virtual override {
        require(operator != _msgSender(), "ERC721: approve to caller");
        _operatorApprovals[_msgSender()][operator] = approved;
        emit ApprovalForAll(_msgSender(), operator, approved);
    }
    function isApprovedForAll(address owner, address operator) public view virtual override returns (bool) { return _operatorApprovals[owner][operator]; }
    function transferFrom(address from, address to, uint256 tokenId) public virtual override {
        require(ERC721.ownerOf(tokenId) == from, "ERC721: transfer of token that is not own");
        require(to != address(0), "ERC721: transfer to the zero address");
        _beforeTokenTransfer(from, to, tokenId);
        _approve(address(0), tokenId);
        _balances[from] -= 1;
        _balances[to] += 1;
        _owners[tokenId] = to;
        emit Transfer(from, to, tokenId);
    }
    function safeTransferFrom(address from, address to, uint256 tokenId) public virtual override { safeTransferFrom(from, to, tokenId, ""); }
    function safeTransferFrom(address from, address to, uint256 tokenId, bytes memory _data) public virtual override {
        transferFrom(from, to, tokenId);
        require(_checkOnERC721Received(from, to, tokenId, _data), "ERC721: transfer to non ERC721Receiver implementer");
    }
    function _exists(uint256 tokenId) internal view virtual returns (bool) { return _owners[tokenId] != address(0); }
    function _safeMint(address to, uint256 tokenId) internal virtual {
        _mint(to, tokenId);
        require(_checkOnERC721Received(address(0), to, tokenId, ""), "ERC721: transfer to non ERC721Receiver implementer");
    }
    function _mint(address to, uint256 tokenId) internal virtual {
        require(to != address(0), "ERC721: mint to the zero address");
        require(!_exists(tokenId), "ERC721: token already minted");
        _beforeTokenTransfer(address(0), to, tokenId);
        _balances[to] += 1;
        _owners[tokenId] = to;
        emit Transfer(address(0), to, tokenId);
    }
    function _burn(uint256 tokenId) internal virtual {
        address owner = ERC721.ownerOf(tokenId);
        _beforeTokenTransfer(owner, address(0), tokenId);
        _approve(address(0), tokenId);
        _balances[owner] -= 1;
        delete _owners[tokenId];
        emit Transfer(owner, address(0), tokenId);
    }
    function _approve(address to, uint256 tokenId) internal virtual {
        _tokenApprovals[tokenId] = to;
        emit Approval(ERC721.ownerOf(tokenId), to, tokenId);
    }
    function _checkOnERC721Received(address from, address to, uint256 tokenId, bytes memory _data) private returns (bool) {
        if (to.isContract()) {
            try IERC721Receiver(to).onERC721Received(_msgSender(), from, tokenId, _data) returns (bytes4 retval) {
                return retval == IERC721Receiver.onERC721Received.selector;
            } catch (bytes memory reason) {
                if (reason.length == 0) {
                    revert("ERC721: transfer to non ERC721Receiver implementer");
                } else { assembly { revert(add(32, reason), mload(reason)) } }
            }
        } else { return true; }
    }
    function _beforeTokenTransfer(address from, address to, uint256 tokenId) internal virtual {}
}
"""

def deploy_and_mint():
    w3 = Web3(Web3.HTTPProvider(RPC_ENDPOINT))
    if not w3.is_connected():
        print("Failed to connect to the blockchain.")
        return
    print(f"Connected to blockchain. Chain ID: {w3.eth.chain_id}")
    install_solc("0.8.0")
    
    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {
            "MyNFT.sol": {"content": SOLIDITY_SOURCE_CODE},
            "@openzeppelin/contracts/token/ERC721/ERC721.sol": {"content": ERC721_SOURCE_CODE},
            "@openzeppelin/contracts/access/Ownable.sol": {"content": OWNABLE_SOURCE_CODE},
            "@openzeppelin/contracts/utils/Context.sol": {"content": CONTEXT_SOURCE_CODE},
            "@openzeppelin/contracts/utils/introspection/ERC165.sol": {"content": ERC165_SOURCE_CODE},
            "@openzeppelin/contracts/utils/introspection/IERC165.sol": {"content": IERC165_SOURCE_CODE},
            "@openzeppelin/contracts/token/ERC721/IERC721.sol": {"content": IERC721_SOURCE_CODE},
            "@openzeppelin/contracts/token/ERC721/IERC721Receiver.sol": {"content": IERC721_RECEIVER_SOURCE_CODE},
            "@openzeppelin/contracts/token/ERC721/IERC721Metadata.sol": {"content": IERC721_METADATA_SOURCE_CODE},
            "@openzeppelin/contracts/utils/Address.sol": {"content": ADDRESS_SOURCE_CODE},
            "@openzeppelin/contracts/utils/Strings.sol": {"content": STRINGS_SOURCE_CODE},
        },
        "settings": { "outputSelection": { "*": { "*": ["abi", "evm.bytecode"] } } },
    }, solc_version="0.8.0")

    if 'errors' in compiled_sol:
        has_errors = False
        for error in compiled_sol['errors']:
            if error['severity'] == 'error':
                print(f"Solidity Compilation Error: {error['formattedMessage']}")
                has_errors = True
        if has_errors:
            return

    bytecode = compiled_sol["contracts"]["MyNFT.sol"]["MyNFT"]["evm"]["bytecode"]["object"]
    abi = compiled_sol["contracts"]["MyNFT.sol"]["MyNFT"]["abi"]
    
    adjective = random.choice(ADJECTIVES)
    noun = random.choice(NOUNS)
    cool_name = f"{adjective} {noun}"
    contract_name = f"{cool_name} Collection"
    token_symbol = "".join([word[0] for word in cool_name.split()]).upper()
    
    print(f"Compilation successful. Deploying contract: {contract_name} ({token_symbol})")
    
    MyNFT = w3.eth.contract(abi=abi, bytecode=bytecode)
    nonce = w3.eth.get_transaction_count(MY_ADDRESS)
    transaction = MyNFT.constructor(contract_name, token_symbol).build_transaction({
        "chainId": CHAIN_ID, "from": MY_ADDRESS, "nonce": nonce, "gasPrice": w3.eth.gas_price,
    })
    
    signed_txn = w3.eth.account.sign_transaction(transaction, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_txn.rawTransaction)
    print(f"Deploying contract, waiting for receipt... TX Hash: {tx_hash.hex()}")
    tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    contract_address = tx_receipt.contractAddress
    print(f"Contract deployed! Address: {contract_address}")
    print(f"View on Block Explorer: https://chainscan-galileo.0g.ai/address/{contract_address}")
    
    nft_contract = w3.eth.contract(address=contract_address, abi=abi)
    mint_nonce = w3.eth.get_transaction_count(MY_ADDRESS)
    mint_txn = nft_contract.functions.safeMint(MY_ADDRESS).build_transaction({
        "chainId": CHAIN_ID, "from": MY_ADDRESS, "nonce": mint_nonce, "gasPrice": w3.eth.gas_price,
    })
    
    signed_mint_txn = w3.eth.account.sign_transaction(mint_txn, private_key=PRIVATE_KEY)
    mint_tx_hash = w3.eth.send_raw_transaction(signed_mint_txn.rawTransaction)
    mint_tx_receipt = w3.eth.wait_for_transaction_receipt(mint_tx_hash)
    print(f"NFT minted successfully! Transaction Hash: {mint_tx_receipt.transactionHash.hex()}")
    print(f"View on Block Explorer: https://chainscan-galileo.0g.ai/tx/{mint_tx_receipt.transactionHash.hex()}")
    print("-" * 40)

def job():
    print(f"Running scheduled job at {time.ctime()}...")
    try:
        deploy_and_mint()
    except Exception as e:
        print(f"An error occurred during the job: {e}")

if __name__ == "__main__":
    job()
    schedule.every().day.at("09:00").do(job) 
    print("Scheduler started. The script will now run daily at the scheduled time.")
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)
        except KeyboardInterrupt:
            print("\nScheduler stopped by user.")
            break
