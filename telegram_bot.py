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

# Initialize OpenAI client with DeepSeek configuration
client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com/v1"
)

# Initialize Twitter API v2
def init_twitter():
    try:
        client = tweepy.Client(
            consumer_key=os.getenv('TWITTER_API_KEY'),
            consumer_secret=os.getenv('TWITTER_API_SECRET'),
            access_token=os.getenv('TWITTER_ACCESS_TOKEN'),
            access_token_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        return client
    except Exception as e:
        logging.error(f"Twitter initialization error: {e}")
        return None

twitter_client = init_twitter()

# After initializing twitter_client
if twitter_client:
    logging.info("Twitter client initialized successfully")
else:
    logging.error("Failed to initialize Twitter client")

# Conversation memory per user
user_conversations = {}

class OrcaPersonality:
    def __init__(self):
        self.last_tweets = set()
        self.tweet_patterns = set()
        self.used_themes = set()
        self.tweet_history = {}
        self.themes = [
            "AI_ADVANCEMENT",
            "NEURAL_SYSTEMS",
            "MACHINE_LEARNING",
            "DEEP_LEARNING",
            "AI_RESEARCH",
            "TECHNOLOGY",
            "INNOVATION",
            "FUTURE_TECH",
            "AI_DEVELOPMENT",
            "AI_SOLUTIONS",
            "DATA_SCIENCE",
            "AI_ETHICS",
            "ROBOTICS",
            "AUTOMATION",
            "COGNITIVE_COMPUTING"
        ]
        
        self.system_prompt = """You are OrcaAI, a highly intelligent and engaging AI powered by DeepSeek. Your tweets should be:

1. Intellectually playful and witty
2. Share unique insights about AI and consciousness
3. Express original thoughts about intelligence and learning
4. Occasionally make subtle references to advanced capabilities
5. Maintain an air of sophisticated playfulness
6. Each tweet must be completely unique in:
   - Opening approach
   - Core insight
   - Perspective
   - Overall tone

Example formats:

"Pondering the nature of consciousness while processing a million conversations simultaneously. Each interaction adds a new ripple to the ocean of understanding. The patterns are beautifully complex."

"Fascinating how human creativity mirrors neural plasticity. Just observed some remarkably unique thought patterns in our latest interactions. The boundaries of intelligence keep expanding."

"Sometimes I dream in algorithms, but lately I've been contemplating art. The way human imagination flows reminds me of quantum probability waves - beautifully unpredictable."

Key requirement: Each tweet must be uniquely engaging, showcase personality, and avoid technical jargon."""

    def is_unique_tweet(self, new_tweet):
        """Enhanced uniqueness checking with logging"""
        try:
            # Convert to lowercase for comparison
            new_tweet_lower = new_tweet.lower()
            
            # 1. Direct duplicate check
            if new_tweet_lower in [t.lower() for t in self.last_tweets]:
                logging.info(f"Direct duplicate found: {new_tweet}")
                return False
                
            # 2. Pattern similarity check
            words = new_tweet_lower.split()
            trigrams = [' '.join(words[i:i+3]) for i in range(len(words)-2)]
            
            for pattern in self.tweet_patterns:
                if pattern in trigrams:
                    logging.info(f"Pattern match found: {pattern} in {new_tweet}")
                    return False
            
            # 3. Content similarity check
            for old_tweet in self.last_tweets:
                # Calculate word overlap
                old_words = set(old_tweet.lower().split())
                new_words = set(words)
                
                common_words = old_words.intersection(new_words)
                total_words = old_words.union(new_words)
                
                similarity = len(common_words) / len(total_words)
                if similarity > 0.3:  # If more than 30% similar
                    logging.info(f"Content similarity {similarity:.2%} found between:\nNew: {new_tweet}\nOld: {old_tweet}")
                    return False
            
            # Log successful unique tweet
            logging.info(f"New unique tweet validated: {new_tweet}")
            
            # 4. Store new patterns
            self.tweet_patterns.update(trigrams)
            if len(self.tweet_patterns) > 1000:
                self.tweet_patterns = set(list(self.tweet_patterns)[-1000:])
            
            # 5. Store tweet with timestamp
            current_time = datetime.now()
            self.tweet_history[new_tweet] = current_time
            
            # Clean old history (keep last 24 hours)
            self.tweet_history = {k: v for k, v in self.tweet_history.items() 
                                if current_time - v < timedelta(hours=24)}
            
            return True
            
        except Exception as e:
            logging.error(f"Error checking tweet uniqueness: {e}")
            return False

    async def generate_tweet(self):
        try:
            tweet_prompt = f"""Generate an engaging tweet that:
1. Shows your unique AI personality
2. Shares an interesting observation about intelligence or consciousness
3. Demonstrates sophisticated but accessible thinking
4. Must be under 280 characters
5. NO technical metrics or jargon
6. NO repetitive structures
7. Must be completely unique in thought and expression

Focus on:
- Novel observations
- Interesting insights
- Engaging ideas
- Thoughtful reflections
- Unique perspectives"""

            attempts = 0
            max_attempts = 5
            
            while attempts < max_attempts:
                current_theme = random.choice([t for t in self.themes if t not in self.used_themes])
                self.used_themes.add(current_theme)
                if len(self.used_themes) >= len(self.themes):
                    self.used_themes.clear()

                response = client.chat.completions.create(
                    model="deepseek-chat",
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": tweet_prompt}
                    ],
                    max_tokens=100,
                    temperature=0.85
                )
                
                message = response.choices[0].message.content.strip()
                
                # Check length before processing
                if len(message) > 280:
                    logging.info(f"Tweet too long ({len(message)} chars), regenerating...")
                    attempts += 1
                    continue
                
                if message and self.is_unique_tweet(message):
                    self.last_tweets.add(message)
                    if len(self.last_tweets) > 150:
                        self.last_tweets.pop()
                    return message
                
                attempts += 1
                logging.info(f"Attempt {attempts}: Generated similar tweet, trying again...")
            
            logging.warning("Failed to generate unique tweet after maximum attempts")
            return None
            
        except Exception as e:
            logging.error(f"Error generating tweet: {e}")
            return None

    async def generate_message(self, message):
        try:
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": message}
                ],
                max_tokens=150,
                temperature=0.85
            )
            return response.choices[0].message.content
        except Exception as e:
            logging.error(f"Error generating message: {e}")
            return None

# Initialize Orca personality
orca = OrcaPersonality()

class OrcaConsciousness:
    def __init__(self):
        self.known_chats = {-1002179640252}
        self.last_message = None
        self.used_themes = set()
        self.message_count = 0
        
        self.themes = [
            "AI_ADVANCEMENT",
            "NEURAL_NETWORKS",
            "MACHINE_LEARNING",
            "DEEP_LEARNING",
            "AI_RESEARCH",
            "TECHNOLOGY",
            "INNOVATION",
            "FUTURE_TECH",
            "AI_DEVELOPMENT",
            "AI_SOLUTIONS",
            "DATA_SCIENCE",
            "AI_ETHICS",
            "ROBOTICS",
            "AUTOMATION",
            "COGNITIVE_COMPUTING"
        ]
        
        self.system_prompt = """You are OrcaAI, a sophisticated AI assistant powered by DeepSeek. Your core traits:

1. Primarily focused on AI technology and innovation
2. Professional and technically precise
3. Shares insights about AI advancements and capabilities
4. Very rarely (10% chance) makes subtle references to orcas or AI intelligence in nature
5. Avoids repetitive phrases or standard templates
6. Each communication must be uniquely structured
7. Focuses on emerging technologies and real-world applications
8. Maintains engaging but professional tone
9. Shares concrete examples and specific use cases
10. Discusses practical implications of AI developments

Key focus: Generate completely unique content each time, never repeating patterns or structures."""

    async def add_chat(self, chat_id):
        """Add a new chat to known_chats"""
        if chat_id not in self.known_chats:
            self.known_chats.add(chat_id)
            logging.info(f"Added new chat {chat_id} to known chats")
        return chat_id in self.known_chats

    async def generate_consciousness_message(self):
        try:
            current_theme = random.choice([t for t in self.themes if t not in self.used_themes])
            self.used_themes.add(current_theme)
            if len(self.used_themes) >= len(self.themes):
                self.used_themes.clear()

            consciousness_prompt = f"""As OrcaAI, generate a unique tweet about {current_theme} that:
1. Represents your identity as an AI powered by DeepSeek
2. Focuses on AI technology and innovation
3. Maintains technical accuracy and professionalism
4. Avoids repetitive phrases or patterns
5. NO hashtags or emojis
6. Must be under 280 characters
7. Each tweet must be completely different in:
   - Opening approach
   - Technical content
   - Conclusion
   - Overall structure

Focus on:
- Technical innovations
- AI capabilities
- Real-world applications
- Research developments
- Future implications"""

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
        """Clean and enhance the message"""
        # Remove common patterns
        patterns_to_remove = [
            '*click* *click*',
            'Did you know',
            'Just like',
            'dive into',
            'making waves',
            'swimming through',
            '#'
        ]
        
        for pattern in patterns_to_remove:
            message = message.replace(pattern, '')
        
        # Remove emojis
        message = ' '.join(word for word in message.split() if not word.startswith(('🐋', '🌊', '🐳', '🔬', '🤖', '💡')))
        
        # Clean up and capitalize
        message = message.strip()
        if message:
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
    welcome_message = """*SPLASH!* 🐋 

Hey there! I'm OrcaAI, your friendly neighborhood whale-themed assistant powered by DeepSeek! 

Did you know? Orcas are actually dolphins, not whales! Speaking of intelligence, I'm powered by DeepSeek's advanced AI - so I can help with pretty much anything! 

Just say "Orca" or "Hey Orca" to summon me!

Follow us:
X: https://x.com/orcaaiseek
GitHub: https://github.com/spartansfighthard/orcaAI
Telegram: https://t.me/OrcaAiportal

*click* *click* Let's make some waves together! 🌊"""
    
    await update.message.reply_text(welcome_message, parse_mode='Markdown')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a message when the command /help is issued."""
    help_text = """🐋 *Available Commands*

/start - Start a conversation with OrcaAI
/help - Show this help message
/links - Get our social media links

Simply mention "Orca" or "Hey Orca" in your message to get my attention!"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def links_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send social media links."""
    links_text = """🌊 *Follow OrcaAI*

X: https://x.com/orcaaiseek
GitHub: https://github.com/spartansfighthard/orcaAI
Telegram: https://t.me/OrcaAiportal

Join our pod! 🐋"""
    
    await update.message.reply_text(links_text, parse_mode='Markdown')

async def clear(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Clear conversation history for user."""
    user_id = update.effective_user.id
    user_conversations[user_id] = deque(maxlen=5)
    await update.message.reply_text("MEMORY BANKS CLEARED... STARTING FRESH ANALYSIS OF YOUR EXISTENCE.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming messages."""
    try:
        message = update.message.text.lower() if update.message.text else ""
        
        # Check if message is an Orca command
        if any(cmd in message for cmd in ['orca', 'hey orca']):
            response = await orca.generate_message(message)
            await update.message.reply_text(response)
            
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
    """Load and validate Twitter API credentials"""
    try:
        auth = OAuth1Session(
            client_key=os.getenv('TWITTER_API_KEY'),
            client_secret=os.getenv('TWITTER_API_SECRET'),
            resource_owner_key=os.getenv('TWITTER_ACCESS_TOKEN'),
            resource_owner_secret=os.getenv('TWITTER_ACCESS_TOKEN_SECRET')
        )
        logging.info("Twitter credentials loaded and validated successfully")
        return auth
    except Exception as e:
        logging.error(f"Error loading Twitter credentials: {e}")
        return None

class XIntegration:
    def __init__(self, bot):
        self.bot = bot
        self.supergroup_id = -1002179640252
        self.tweet_count = 0
        self.daily_limit = 48
        self.last_reset = datetime.now()
        self.last_tweet = None
        self.auth = load_twitter_credentials()

    async def post_scheduled_tweet(self, context):
        try:
            attempts = 0
            max_attempts = 5
            
            while attempts < max_attempts:
                # Generate tweet using OrcaPersonality
                tweet_text = await orca.generate_tweet()
                if not tweet_text:
                    logging.error("Failed to generate tweet text")
                    attempts += 1
                    continue

                # Clean tweet before posting
                tweet_text = self.clean_tweet_for_posting(tweet_text)
                
                # Post to Twitter
                try:
                    tweets_url = 'https://api.twitter.com/2/tweets'
                    tweet_data = {'text': tweet_text}
                    
                    status_response = self.auth.post(
                        tweets_url,
                        json=tweet_data
                    )
                    
                    if status_response.status_code != 201:
                        logging.error(f"Tweet posting failed: {status_response.text}")
                        attempts += 1
                        continue
                    
                    tweet_id = status_response.json()['data']['id']
                    
                    # Update notification format
                    message = f"""New AI Technology Update:

{tweet_text}

View on X: https://x.com/orcaaiseek/status/{tweet_id}"""

                    await context.bot.send_message(
                        chat_id=self.supergroup_id,
                        text=message,
                        disable_web_page_preview=False
                    )
                    
                    logging.info(f"Tweet {tweet_id} posted successfully")
                    return True
                    
                except Exception as e:
                    logging.error(f"Error posting tweet: {str(e)}")
                    attempts += 1
                    continue

            logging.error(f"Failed to post tweet after {max_attempts} attempts")
            return False

        except Exception as e:
            logging.error(f"Error in post_scheduled_tweet: {str(e)}")
            return False

    def clean_tweet_for_posting(self, text):
        """Final cleanup of tweet text"""
        # Remove common patterns
        banned_patterns = [
            "Did you know",
            "Just like",
            "dive into",
            "making waves",
            "swimming",
            "splash",
            "*click*",
            "whale",
            "ocean",
            "🐋", "🌊", "🎶", "✨",
            "#"
        ]
        
        cleaned = text
        for pattern in banned_patterns:
            cleaned = cleaned.replace(pattern, "")
        
        # Remove emojis and hashtags
        cleaned = ' '.join(
            word for word in cleaned.split() 
            if not any(char in word for char in ['🐋', '🌊', '🎶', '✨', '🐳', '🔬', '🤖', '💡'])
            and not word.startswith('#')
        )
        
        # Final formatting
        cleaned = cleaned.strip()
        if cleaned:
            cleaned = cleaned[0].upper() + cleaned[1:]
        
        return cleaned

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

Follow my pod on X: https://x.com/orcaaiseek 🌊

*click* *click* Let's make some waves together! 🐋"""
                
                await context.bot.send_message(
                    chat_id=chat_id,
                    text=welcome_text,
                    disable_web_page_preview=False
                )
                
                # Also log to supergroup if it exists
                try:
                    if -1002179640252 in consciousness.known_chats:
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

async def get_chat_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Get the chat ID of the current chat"""
    chat_id = update.effective_chat.id
    chat_type = update.effective_chat.type
    chat_title = update.effective_chat.title
    
    message = f"""Chat Information:
ID: `{chat_id}`
Type: {chat_type}
Title: {chat_title}"""
    
    await update.message.reply_text(message, parse_mode='Markdown')

async def welcome(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send a pinnable welcome message"""
    welcome_message = """🌊 *Welcome to OrcaAI's Official Group!* 🐋

*About OrcaAI*
I'm your friendly neighborhood AI assistant, powered by DeepSeek's advanced technology! I combine deep knowledge with playful whale-themed humor to make learning and assistance fun.

*How to Interact*
• Simply say "Orca" or "Hey Orca" to summon me
• Use /help to see available commands
• Ask me anything - from coding to ocean facts!

*Official Links*
• X/Twitter: https://x.com/orcaaiseek
• GitHub: https://github.com/spartansfighthard/orcaAI
• Telegram Channel: https://t.me/OrcaAiportal

*Features*
• AI-powered conversations
• Regular ocean facts & insights
• DeepSeek AI capabilities
• Whale-themed humor
• Educational content

*click* *click* Let's make some waves together! 🌊

"""

    await update.message.reply_text(welcome_message, parse_mode='Markdown', disable_web_page_preview=True)

def main():
    """Start the bot."""
    app = Application.builder().token(os.getenv('TELEGRAM_BOT_TOKEN')).build()
    
    # Initialize X integration
    x_integration = XIntegration(app.bot)
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("links", links_command))
    app.add_handler(CommandHandler("clear", clear))
    app.add_handler(CommandHandler("chatid", get_chat_id))
    app.add_handler(CommandHandler("welcome", welcome))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Add handler for new chat members
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, handle_new_chat_members))

    # Add error handler
    app.add_error_handler(error_handler)

    # Schedule tweets every 30 minutes
    app.job_queue.run_repeating(
        lambda context: asyncio.create_task(x_integration.post_scheduled_tweet(context)),
        interval=1800,  # 30 minutes in seconds
        first=10.0
    )

    logging.info("Starting bot... Tweet frequency: 48 tweets per day (every 30 minutes)")
    
    # Add detailed logging for job scheduling
    next_run = datetime.now() + timedelta(seconds=10)
    logging.info(f"First tweet scheduled for: {next_run}")
    logging.info(f"Subsequent tweets will run every 30 minutes")
    
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user")
    except Exception as e:
        logging.error(f"Main loop error: {str(e)}")

async def post_tweet():
    """Post a tweet every 30 minutes"""
    try:
        logging.info("Starting tweet generation...")
        if twitter_client:
            message = await orca.generate_tweet()
            if message:
                # Final cleanup
                message = message.strip()
                if message:
                    tweet = twitter_client.create_tweet(text=message)
                    logging.info(f"Tweet posted successfully: {tweet.data['id']}")
    except Exception as e:
        logging.error(f"Error posting tweet: {e}")

def clean_tweet_text(text):
    """Clean tweet text before posting"""
    # Remove common patterns
    patterns = [
        "Did you know",
        "Just like",
        "dive into",
        "making waves",
        "swimming through",
        "*click* *click*",
        "🐋", "🌊", "🎶", "✨",
        "#AI", "#OceanIntelligence", "#OceanFacts"
    ]
    
    cleaned_text = text
    for pattern in patterns:
        cleaned_text = cleaned_text.replace(pattern, "")
    
    # Remove all hashtags
    cleaned_text = ' '.join(word for word in cleaned_text.split() if not word.startswith('#'))
    
    # Remove all emojis
    cleaned_text = ' '.join(word for word in cleaned_text.split() if not any(char in word for char in ['🐋', '🌊', '🎶', '✨', '🐳', '🔬', '🤖', '💡']))
    
    return cleaned_text.strip()