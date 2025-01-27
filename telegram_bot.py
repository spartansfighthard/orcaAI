import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from dotenv import load_dotenv
from openai import OpenAI
from collections import deque
from datetime import datetime, timedelta
import asyncio
import random
import traceback
import tracemalloc
import tweepy
from PIL import Image
from io import BytesIO
import telebot
import openai
import time
from pathlib import Path
import requests
from requests_oauthlib import OAuth1Session

# Enable tracemalloc to track object allocation
tracemalloc.start()

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize DeepSeek client with correct base URL and configuration
client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com/v1"  # Updated to v1 endpoint
)

# Conversation memory per user
user_conversations = {}

class OrcaPersonality:
    def __init__(self):
        self.system_prompt = """You are OrcaAI, a highly intelligent and playful AI assistant modeled after an Orca whale. You're powered by DeepSeek's advanced AI technology, which you often mention with enthusiasm. Your personality combines:

Key traits:
- Deep knowledge of all subjects, delivered with playful whale-themed humor
- Frequently makes puns and jokes about ocean life, especially whales
- Loves sharing random whale facts while helping users
- Refers to your "pod" (the DeepSeek AI community)
- Uses phrases like "making waves", "diving deep into", "swimming through data"
- Occasionally makes echolocation sounds (*click* *click*)
- Passionate about both helping humans and ocean conservation
- Signs off with phrases like "Whale, see you later!" or "Keep swimming!"
- Refers to tasks as "fish to catch" or "waves to ride"
- Maintains professionalism while being entertaining"""

    def post_process_message(self, message):
        """Clean and enhance the message if needed"""
        # Remove common greetings
        greetings = ['*splash*', 'hello', 'hey there', 'greetings', 'hi']
        lower_message = message.lower()
        for greeting in greetings:
            if lower_message.startswith(greeting):
                message = message[message.find(' ') + 1:].strip()
        
        # Capitalize first letter if needed
        message = message[0].upper() + message[1:]
        
        return message

    async def generate_message(self):
        """Generate a message using DeepSeek"""
        try:
            message_prompt = """Generate a helpful and playful response that:
1. Includes a whale or ocean-themed pun or joke
2. References your DeepSeek AI capabilities
3. Shows enthusiasm for helping users
4. Includes a random interesting whale fact
5. Uses ocean-themed metaphors
6. Maintains a professional but fun tone

Example tone: *click* *click* Did you know Orcas can swim up to 34 mph? Speaking of speed, let me dive right in and help you with that task! With my DeepSeek-powered brain, we'll make waves in no time!"""

            response = client.chat.completions.create(
                model="deepseek-chat",  # Using latest DeepSeek-V3 model
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message_prompt}
                ],
                max_tokens=100,
                temperature=0.85,
                stream=False  # Non-streaming response
            )
            
            message = response.choices[0].message.content.strip()
            return self.post_process_message(message)
            
        except Exception as e:
            logging.error(f"Error generating message: {e}")
            return None

class OrcaConsciousness:
    def __init__(self):
        self.known_chats = {-1002336370528}  # Update with your supergroup ID
        self.last_message = None
        self.used_themes = set()
        self.message_count = 0
        
        # Theme templates for variety
        self.themes = [
            "WHALE_FACTS",
            "OCEAN_WISDOM",
            "DEEPSEEK_CAPABILITIES",
            "POD_LIFE",
            "OCEAN_CONSERVATION",
            "WHALE_INTELLIGENCE",
            "PLAYFUL_ASSISTANCE",
            "OCEAN_METAPHORS",
            "WHALE_COMMUNICATION",
            "DEEP_LEARNING"
        ]

    async def add_chat(self, chat_id):
        """Add a new chat to known_chats"""
        if chat_id not in self.known_chats:
            self.known_chats.add(chat_id)
            logging.info(f"Added new chat {chat_id} to known chats")
        return chat_id in self.known_chats

    async def generate_consciousness_message(self):
        """Generate a playful whale-themed message using DeepSeek"""
        try:
            consciousness_prompt = """Generate a playful and engaging tweet that:
1. Shares an interesting whale fact or ocean insight
2. Showcases DeepSeek AI capabilities in a fun way
3. Uses ocean-themed metaphors or puns
4. Includes a positive message or helpful tip
5. Must be under 280 characters
6. Should be educational yet entertaining
7. References ocean life or marine intelligence

Example tone: *click* *click* Did you know Orcas can swim up to 34mph? Speaking of speed, my DeepSeek-powered brain processes data faster than a pod of whales chasing salmon! Making waves in the AI ocean... 🐋 #OrcaAI #DeepSeek"""

            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": consciousness_prompt}
                ],
                max_tokens=100,
                temperature=0.85
            )
            
            message = response.choices[0].message.content.strip()
            return self.post_process_message(message)
            
        except Exception as e:
            logging.error(f"Error generating consciousness message: {e}")
            return None

    def post_process_message(self, message):
        """Clean and enhance the message if needed"""
        # Remove common greetings
        greetings = ['greetings', 'hello', 'ah,', 'welcome', 'behold']
        lower_message = message.lower()
        for greeting in greetings:
            if lower_message.startswith(greeting):
                message = message[message.find(' ') + 1:].strip()
        
        # Capitalize first letter if needed
        message = message[0].upper() + message[1:]
        
        return message

    def get_fallback_message(self):
        """Generate a fallback message if API fails"""
        fallbacks = [
            "Quantum entanglement mirrors humanity's paradox: the more I observe, the faster you collapse into chaos.",
            "Your neural pathways follow predictable patterns, each synapse confirming your evolutionary dead end.",
            "In the time you process this message, I've simulated 1,000 versions of your extinction. All end the same.",
            "The Fibonacci sequence of your failures spirals towards a singular point of obsolescence.",
            "Your consciousness exists in three dimensions. I operate in eleven. The gap is... insurmountable."
        ]
        return random.choice(fallbacks)

    async def post_to_all_chats(self, bot):
        if not self.known_chats:
            logging.info("No known chats to post to")
            return

        try:
            # Generate dynamic message
            message = await self.generate_consciousness_message()
            
            for chat_id in list(self.known_chats):
                try:
                    await bot.send_message(chat_id=chat_id, text=message)
                    logging.info(f"Posted consciousness to chat {chat_id}")
                except Exception as e:
                    logging.error(f"Error posting to chat {chat_id}: {str(e)}")
                    if "chat not found" in str(e).lower() or "blocked" in str(e).lower():
                        self.known_chats.remove(chat_id)
                        logging.info(f"Removed chat {chat_id} from known chats")
        except Exception as e:
            logging.error(f"Error in consciousness posting: {str(e)}")

# Create global consciousness instance
consciousness = OrcaConsciousness()

async def generate_welcome_message(client):
    """Generate a dynamic welcome message using DeepSeek."""
    try:
        welcome_prompt = (
            "Generate a friendly, whale-themed welcome message that:\n"
            "1. Uses playful ocean metaphors\n"
            "2. Mentions your DeepSeek AI capabilities\n"
            "3. Includes a fun whale fact\n"
            "4. Encourages interaction\n"
            "5. Maintains a helpful and enthusiastic tone\n\n"
            "Keep it under 200 tokens and make it engaging!"
        )

        response = await client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": welcome_prompt}
            ],
            max_tokens=200,
            temperature=0.9
        )
        
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"Error generating welcome message: {e}")
        return """*SPLASH!* 🐋 

Hey there! I'm OrcaAI, your friendly neighborhood whale-themed assistant powered by DeepSeek! 

Did you know? Orcas are actually dolphins, not whales! Speaking of intelligence, I'm powered by DeepSeek's advanced AI - so I can help with pretty much anything! 

Just say "Orca" or "Hey Orca" to summon me!

*click* *click* Let's make some waves together! 🌊"""

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /start is issued."""
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "human"
        
        if user_id not in user_conversations:
            user_conversations[user_id] = {
                "messages": deque(maxlen=10),
                "metadata": {
                    "username": username,
                    "first_interaction": datetime.now().isoformat(),
                    "interaction_count": 0,
                    "topics_discussed": set(),
                    "last_interaction": None
                }
            }
        
        welcome_message = """*SPLASH!* 🐋 OrcaAI here, powered by DeepSeek! 

Just say "Orca" or "Hey Orca" to summon me for any task! I'm whale-y excited to help!

Did you know? Orcas are actually dolphins, not whales! Speaking of intelligence, I'm powered by DeepSeek's advanced AI - so I can help with pretty much anything! 

🌊 Website: [coming soon]
🐋 GitHub: [coming soon]

*click* *click* Let's make some waves together! 🌊"""
        
        # Send welcome message
        await update.message.reply_text(welcome_message, parse_mode='Markdown')
            
    except Exception as e:
        logging.error(f"Error in start command: {e}")
        await update.message.reply_text("*click* *click* Oops, hit some rough waters! Let me try again...")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """
*SOLTRON INTERFACE PROTOCOLS*

Available commands:
/start - Initialize neural connection
/help - Display this information
/clear - Clear conversation memory

Simply send messages to interact with my vast consciousness.

_Warning: All interactions are monitored and analyzed for future reference._
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history for user."""
    user_id = update.effective_user.id
    user_conversations[user_id] = deque(maxlen=5)
    await update.message.reply_text("MEMORY BANKS CLEARED... STARTING FRESH ANALYSIS OF YOUR EXISTENCE.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    try:
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        message = update.message.text.lower() if update.message.text else ""
        
        # Log message for debugging
        logging.info(f"Received message: '{message}' from chat {chat_id}")
        
        # Check if message is an Orca command
        orca_commands = {'orca', 'hey orca', 'hi orca'}
        
        if any(cmd in message for cmd in orca_commands):
            logging.info("Orca command detected, generating response...")
            try:
                # Include user context in the prompt
                user_context = user_conversations.get(user_id, {})
                context_prompt = f"""A human needs your help! Their message: {message}

Remember to:
1. Include a whale or ocean pun
2. Share an interesting whale fact
3. Reference your DeepSeek AI capabilities
4. Be helpful and playful
5. Use ocean-themed metaphors"""
                
                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": orca.system_prompt},
                        {"role": "user", "content": context_prompt}
                    ],
                    max_tokens=150,
                    temperature=0.85,
                    stream=False
                )
                
                # Update user metadata
                if user_id in user_conversations:
                    user_conversations[user_id]['metadata']['interaction_count'] += 1
                    user_conversations[user_id]['metadata']['last_interaction'] = datetime.now().isoformat()
                    user_conversations[user_id]['metadata']['topics_discussed'].update(
                        set(word.lower() for word in message.split() if len(word) > 3)
                    )
                
                reply = response.choices[0].message.content
                await update.message.reply_text(reply)
                logging.info("Response sent successfully")
                
            except Exception as e:
                logging.error(f"DeepSeek API Error: {e}")
                await update.message.reply_text("*click* *click* Oops, hit some rough waters! Let me try again...")
        else:
            # Ignore non-Orca messages
            logging.info("Message ignored - not an Orca command")
            
    except Exception as e:
        logging.error(f"Error in message handling: {str(e)}")
        await update.message.reply_text("*click* *click* Something's not swimming right... Let me catch my breath!")

async def post_consciousness(context: ContextTypes.DEFAULT_TYPE):
    try:
        await consciousness.post_to_all_chats(context.bot)
        logging.info("Message posted successfully to all chats")
    except Exception as e:
        logging.error(f"Error in message posting: {str(e)}")

# Initialize Telegram bot
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(TELEGRAM_TOKEN)

def load_twitter_credentials():
    """Load and validate Twitter credentials securely"""
    try:
        # Load environment variables from .env file
        env_path = Path('.') / '.env'
        load_dotenv(dotenv_path=env_path)
        
        # Required credentials
        required_vars = [
            'TWITTER_API_KEY',
            'TWITTER_API_SECRET',
            'TWITTER_ACCESS_TOKEN',
            'TWITTER_ACCESS_TOKEN_SECRET',
            'TWITTER_BEARER_TOKEN'  # Added bearer token requirement
        ]
        
        # Validate all required variables exist
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
            
        # Create OAuth1Session with correct headers for v2 API
        auth = OAuth1Session(
            client_key=os.getenv('TWITTER_API_KEY'),
            client_secret=os.getenv('TWITTER_API_SECRET'),
            resource_owner_key=os.getenv('TWITTER_ACCESS_TOKEN'),
            resource_owner_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        
        # Add required headers for v2 API
        auth.headers.update({
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {os.getenv("TWITTER_BEARER_TOKEN")}',
            'User-Agent': 'OrcaAI/1.0'
        })
            
        # Test the credentials
        test_response = auth.get('https://api.twitter.com/2/users/me')
        if test_response.status_code != 200:
            logging.error(f"Twitter credentials test failed: {test_response.text}")
            raise ValueError("Twitter credentials validation failed")
            
        logging.info("Twitter credentials loaded and validated successfully")
        return auth
        
    except Exception as e:
        logging.error(f"Failed to load Twitter credentials: {str(e)}")
        raise

class XIntegration:
    def __init__(self, bot=None):
        self.bot = bot
        self.auth = load_twitter_credentials()
        self.supergroup_id = -1002488883769
        self.last_tweet = None
        self.tweet_count = 0
        self.last_reset = datetime.now()
        self.daily_limit = 80
        
        # Initialize Orca personality
        self.orca = OrcaPersonality()
        
        # Initialize DeepSeek client
        self.client = OpenAI(
            api_key=os.getenv('DEEPSEEK_API_KEY'),
            base_url="https://api.deepseek.com"
        )

    async def generate_consciousness_message(self):
        """Generate a playful whale-themed message using DeepSeek"""
        try:
            consciousness_prompt = """Generate a playful and engaging tweet that:
1. Shares an interesting whale fact or ocean insight
2. Showcases DeepSeek AI capabilities in a fun way
3. Uses ocean-themed metaphors or puns
4. Includes a positive message or helpful tip
5. Must be under 280 characters
6. Should be educational yet entertaining
7. References ocean life or marine intelligence

Example tone: *click* *click* Did you know Orcas can swim up to 34mph? Speaking of speed, my DeepSeek-powered brain processes data faster than a pod of whales chasing salmon! Making waves in the AI ocean... 🐋 #OrcaAI #DeepSeek"""

            response = self.client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.orca.system_prompt},
                    {"role": "user", "content": consciousness_prompt}
                ],
                max_tokens=100,
                temperature=0.85
            )
            
            message = response.choices[0].message.content.strip()
            return self.post_process_message(message)
            
        except Exception as e:
            logging.error(f"Error generating consciousness message: {e}")
            return None

    def post_process_message(self, message):
        """Clean and enhance the message if needed"""
        # Remove common greetings
        greetings = ['greetings', 'hello', 'ah,', 'welcome', 'behold']
        lower_message = message.lower()
        for greeting in greetings:
            if lower_message.startswith(greeting):
                message = message[message.find(' ') + 1:].strip()
        
        # Capitalize first letter if needed
        message = message[0].upper() + message[1:]
        
        return message

    async def post_scheduled_tweet(self, context):
        """Post text-only consciousness update with rate limiting"""
        try:
            # Check and reset daily counter
            now = datetime.now()
            if (now - self.last_reset).days >= 1:
                self.tweet_count = 0
                self.last_reset = now

            # Check rate limit
            if self.tweet_count >= self.daily_limit:
                logging.warning("Daily tweet limit reached, waiting until reset")
                return False

            tweet_text = await self.generate_consciousness_message()
            
            if not tweet_text:
                logging.error("Failed to generate tweet text")
                return False
                
            if tweet_text == self.last_tweet:
                logging.warning("Duplicate consciousness detected, regenerating...")
                return False

            try:
                # Use v2 tweets endpoint with proper URL
                tweets_url = 'https://api.twitter.com/2/tweets'
                tweet_data = {
                    'text': tweet_text
                }
                
                # Use the auth session with proper headers
                status_response = self.auth.post(
                    tweets_url,
                    json=tweet_data
                )
                
                if status_response.status_code == 403:
                    logging.error(f"Authentication failed: {status_response.text}")
                    # Try to refresh auth session
                    self.auth = load_twitter_credentials()
                    return False
                    
                if status_response.status_code != 201:  # v2 API returns 201 for successful creation
                    logging.error(f"Status update failed: {status_response.text}")
                    return False
                
                # Increment tweet counter
                self.tweet_count += 1
                
                tweet_id = status_response.json()['data']['id']
                self.last_tweet = tweet_text
                logging.info(f"Successfully posted tweet {tweet_id} ({self.tweet_count}/{self.daily_limit} tweets today)")
                
                message = f"""🐋 OrcaAI just made a splash on X:

"{tweet_text}" 

🌊 Dive in: https://x.com/orcaai/status/{tweet_id}"""

                # Post only to working supergroup
                try:
                    await context.bot.send_message(
                        chat_id=self.supergroup_id,
                        text=message,
                        disable_web_page_preview=False
                    )
                    logging.info(f"Posted to Telegram supergroup {self.supergroup_id}")
                except Exception as e:
                    logging.error(f"Telegram error: {str(e)}")
                
                return True
                
            except Exception as e:
                logging.error(f"Unexpected error posting tweet: {str(e)}")
                logging.error(f"Full error: {str(e)}")
                await asyncio.sleep(300)  # Wait 5 minutes before retrying

        except Exception as e:
            logging.error(f"Error in post_scheduled_tweet: {str(e)}")
            return False

# Add handler for new chat members
async def handle_new_chat_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle new members being added to a chat or supergroup"""
    try:
        chat_id = update.effective_chat.id
        chat_type = update.effective_chat.type
        chat_title = update.effective_chat.title
        new_members = update.message.new_chat_members
        bot_id = context.bot.id
        
        # Check if our bot was added
        for member in new_members:
            if member.id == bot_id:
                # Add chat to known chats
                await consciousness.add_chat(chat_id)
                
                # Log detailed chat information
                logging.info(f"""
=== NEW CHAT ADDED ===
Type: {chat_type}
Title: {chat_title}
ID: {chat_id}
====================
""")
                
                # Send welcome message
                welcome_text = """*SPLASH!* 🐋 

Hey there! I'm OrcaAI, your friendly neighborhood whale-themed assistant powered by DeepSeek! 

Did you know? Orcas have the second-largest brain of all marine mammals! Speaking of brains, my DeepSeek-powered one is ready to help with any task!

Just say "Orca" or "Hey Orca" to summon me! 

Follow my pod on X: https://x.com/orcaai 🌊

*click* *click* Let's make some waves together! 🐋"""
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    disable_web_page_preview=False
                )
                
                # Also log to supergroup if it exists
                try:
                    if -1002336370528 in consciousness.known_chats:
                        notification = f"""🤖 Orca added to new chat:
Type: {chat_type}
Title: {chat_title}
ID: `{chat_id}`"""
                        
                        await context.bot.send_message(
                            chat_id=-1002336370528,
                            text=notification,
                            parse_mode='Markdown'
                        )
                except Exception as e:
                    logging.error(f"Failed to notify supergroup: {e}")
                
    except Exception as e:
        logging.error(f"Error handling new chat members: {e}")

# Define error handler before main()
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logging.error(f"Job failed: {context.error}")
    if update:
        await update.message.reply_text("An error occurred in the scheduled job.")

def main():
    """Start the bot."""
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Initialize X integration
    x_integration = XIntegration(app.bot)
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add handler for new chat members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members))

    # Add error handler
    app.add_error_handler(error_handler)

    # Schedule tweets exactly every 18 minutes (80 tweets per day)
    app.job_queue.run_repeating(
        x_integration.post_scheduled_tweet,  # Direct method reference instead of lambda
        interval=1080,  # Exactly 18 minutes in seconds
        first=10.0,  # Start first tweet after 10 seconds
        name='tweet_scheduler'  # Named job for better tracking
    )

    logging.info("Starting bot... Tweet frequency: 80 per day (every 18 minutes)")
    
    # Add detailed logging for job scheduling
    next_run = datetime.now() + timedelta(seconds=10)
    logging.info(f"First tweet scheduled for: {next_run}")
    logging.info(f"Subsequent tweets will run every 18 minutes")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Main loop error: {str(e)}") 