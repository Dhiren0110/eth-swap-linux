import asyncio
import logging
from telethon import TelegramClient, events
from config import TELEGRAM_API_ID, TELEGRAM_API_HASH, GROUP_NAMES
from trade import execute_swap

# Configure logging
logging.basicConfig(level=logging.INFO)

client = TelegramClient("bot_session", TELEGRAM_API_ID, TELEGRAM_API_HASH)

# Known stablecoin or non-tradeable contract addresses (for Ethereum)
STABLECOIN_CONTRACTS = {
    "0xdac17f958d2ee523a2206206994597c13d831ec7",  # USDT
    "0xa0b86991c6218b36c1d19d4a2e9eb0ce3606eb48",  # USDC
    "0xeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee",  # Native ETH
}

def extract_hyperlink_from_entities(entities, message_text):
    """
    Extract the first Ethereum contract address from message hyperlinks.
    """
    for entity in entities:
        if hasattr(entity, "url") and "etherscan.io/address/" in entity.url:
            logging.info(f"Hyperlink detected: {entity.url}")
            return entity.url.split("/")[-1]  # Extract the contract address
    return None

@client.on(events.NewMessage)
async def handler(event):
    """
    Process messages containing trade signals or direct contract addresses.
    """
    try:
        # Ensure the message is from a tracked group
        group_name = event.chat.title.strip() if hasattr(event.chat, 'title') else "unknown"
        if group_name not in GROUP_NAMES:
            return  # Ignore messages from untracked groups

        logging.info(f"Processing message from group: {group_name}")

        # Check if "Trade detected:" is in the message
        if "Trade detected:" in event.raw_text:
            # Extract hyperlink from entities
            contract_address = extract_hyperlink_from_entities(event.message.entities, event.raw_text)
            if contract_address:
                logging.info(f"Contract Address Extracted: {contract_address}")

                # Skip if the contract address belongs to known stablecoins or native ETH
                if contract_address.lower() in STABLECOIN_CONTRACTS:
                    logging.info(f"Stablecoin or native ETH detected ({contract_address}). Skipping trade.")
                    return

                # Execute the trade
                success = await execute_swap(contract_address)
                if success:
                    logging.info(f"Trade executed successfully for contract {contract_address}.")
                else:
                    logging.error(f"Trade failed for contract {contract_address}.")
            else:
                logging.warning("No valid contract address found in the message.")
    except Exception as e:
        logging.error(f"Error in handler: {e}")

async def main():
    """
    Start the Telegram bot.
    """
    await client.start()
    logging.info("Bot started. Monitoring messages...")
    async with client:
        await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
