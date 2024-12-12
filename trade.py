import asyncio
import os
import requests
import logging
from dotenv import load_dotenv
from web3 import Web3

# Configure logging
logging.basicConfig(
    level=logging.INFO,  # Set to INFO to reduce detailed debug logs
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("trade_log.log"),
        logging.StreamHandler()
    ]
)

# Apply SelectorEventLoopPolicy for Windows compatibility
if asyncio.get_event_loop_policy().__class__.__name__ != "SelectorEventLoopPolicy":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# Load environment variables
load_dotenv()

# Load Ethereum credentials
rpc_url = os.getenv("rpc_url")
public_key = os.getenv("public_key")
private_key = os.getenv("private_key")
api_key = os.getenv("ONEINCH_API_KEY")
amount_eth = float(os.getenv("AMOUNT_ETH", 0.01))  # Default to 0.01 ETH
simulate = os.getenv("SIMULATE", "true").lower() == "true"

if not all([rpc_url, public_key, private_key, api_key]):
    logging.error("Missing required environment variables.")
    raise ValueError("Missing required environment variables.")

# Web3 instance
web3 = Web3(Web3.HTTPProvider(rpc_url))
if not web3.is_connected():
    logging.error("Failed to connect to Ethereum network.")
    raise ConnectionError("Failed to connect to Ethereum network.")

logging.info("Connected to Ethereum network.")

async def execute_swap(to_token_contract):
    """
    Execute a token swap on Ethereum using the 1inch API.
    :param to_token_contract: Contract address of the token to swap to.
    """
    max_retries = 5
    retry_delay = 2  # seconds
    slippage = 1.0  # 1% slippage
    amount = web3.to_wei(amount_eth, "ether")  # Amount of ETH to swap (in Wei)

    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}: Swapping ETH to {to_token_contract}...")

            # Prepare 1inch API call
            chain_id = "1"  # Ethereum Mainnet
            api_base_url = f"https://api.1inch.dev/swap/v6.0/{chain_id}"
            url = f"{api_base_url}/swap"
            headers = {
                "Authorization": f"Bearer {api_key}",
                "accept": "application/json"
            }
            params = {
                "fromTokenAddress": "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE",  # ETH
                "toTokenAddress": to_token_contract,
                "amount": amount,
                "fromAddress": public_key,
                "slippage": slippage,
                "disableEstimate": "true",
            }

            # Make API request
            response = requests.get(url, headers=headers, params=params)
            logging.info(f"1inch API response status: {response.status_code}")

            if response.status_code != 200:
                raise ValueError(f"1inch API Error: {response.status_code}, {response.text}")

            swap_data = response.json().get("tx")

            if not swap_data:
                raise ValueError("Failed to retrieve transaction data from 1inch API. Response: " + response.text)

            if simulate:
                logging.info("Simulation mode active. Transaction not broadcast.")
                logging.info(f"Transaction Data: {swap_data}")
                return True

            # Sign and broadcast transaction
            transaction = {
                "to": swap_data["to"],
                "data": swap_data["data"],
                "value": int(swap_data["value"]),
                "gas": int(swap_data["gas"]),
                "gasPrice": int(swap_data["gasPrice"]),
                "nonce": web3.eth.get_transaction_count(public_key),
            }

            signed_tx = web3.eth.account.sign_transaction(transaction, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)

            logging.info(f"Transaction Successful! Hash: {web3.to_hex(tx_hash)}")
            logging.info(f"View on Etherscan: https://etherscan.io/tx/{web3.to_hex(tx_hash)}")
            return True

        except Exception as e:
            logging.error(f"Swap attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                logging.info("Retrying...")
                await asyncio.sleep(retry_delay)

    logging.error("All retry attempts failed.")
    return False

# Main execution block
if __name__ == "__main__":
    token_contract = os.getenv("TO_TOKEN_CONTRACT")
    if not token_contract:
        logging.error("No token contract address provided in environment variables.")
        exit(1)

    logging.info("Starting token swap process.")
    asyncio.run(execute_swap(token_contract))
    logging.info("Process completed.")
