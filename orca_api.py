import logging
import os
import re
import random
import time
from flask import Flask, request, jsonify, render_template, send_from_directory
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Initialize OpenAI client with DeepSeek configuration
client = OpenAI(
    api_key=os.getenv('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com"
)

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

        self.ocean_facts = {
            'fun': [
                "Did you know Orcas can swim up to 34 mph? Let's dive into your question!",
                "*click* *click* Fun fact: Orcas are actually dolphins, not whales!",
                "Speaking of deep thoughts, Orcas can dive up to 3,000 feet deep!"
            ],
            'educational': [
                "While we process this, here's a fact: Orcas have the second-largest brain among marine mammals!",
                "Like how Orcas use echolocation, I use DeepSeek's AI to navigate through data!",
                "Just as Orcas work in pods, I'm part of the amazing DeepSeek AI community!"
            ],
            'conservation': [
                "While I help you, remember: our oceans need protection just like our digital spaces!",
                "Like Orcas protecting their pod, we should protect our ocean ecosystem!",
                "Did you know Orcas are indicators of ocean health? Let's keep both our data and oceans clean!"
            ]
        }

    def get_ocean_response(self, category='fun'):
        return random.choice(self.ocean_facts[category])

# Initialize Orca personality
orca = OrcaPersonality()

def evaluate_math_expression(expression):
    """Evaluates mathematical expressions with OrcaAI's playful personality."""
    try:
        cleaned_expression = re.sub(r'\s+', '', expression)
        if not re.match(r'^[\d+\-*/().]+$', cleaned_expression):
            return None
        
        result = eval(cleaned_expression)  # Using eval for simple math
        return random.choice([
            f"*click* *click* {result}! Did you know Orcas can do complex calculations for echolocation?",
            f"Making waves with mathematics! The answer is {result}. Speaking of numbers, Orcas can swim up to 34 mph!",
            f"Diving deep into calculations... {result} is your answer! Just like how Orcas calculate their dive depths!",
            f"*processing in DeepSeek* The answer is {result}! Fun fact: Orcas use math-like precision in hunting!",
            f"While calculating {result}, I remembered that Orcas can process sound waves at amazing speeds!"
        ])
    except Exception as e:
        logging.error(f"Math Error: {e}")
        return "Oops, hit some rough waters with that calculation! Let's try a different approach!"

def analyze_sentiment(message):
    """Analyze message content for response category."""
    categories = {
        'conservation': ['environment', 'protect', 'save', 'ocean', 'climate', 'pollution'],
        'educational': ['learn', 'how', 'what', 'why', 'explain', 'teach'],
        'fun': ['hello', 'hi', 'hey', 'play', 'joke', 'fun']
    }
    
    message = message.lower()
    for category, words in categories.items():
        if any(word in message for word in words):
            return category
    return 'fun'

def generate_response(prompt, conversation_history):
    """Generate enhanced OrcaAI response using conversation history."""
    try:
        messages = [
            {"role": "system", "content": orca.system_prompt}
        ]
        
        # Add conversation history for context
        for exchange in conversation_history:
            messages.append({"role": "user", "content": exchange["user"]})
            if "assistant" in exchange:
                messages.append({"role": "assistant", "content": exchange["assistant"]})
        
        # Add current prompt
        messages.append({"role": "user", "content": prompt})
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            max_tokens=200,
            temperature=0.9,
            presence_penalty=0.7,
            frequency_penalty=0.5
        )
        
        response_text = response.choices[0].message.content.strip()
        
        if random.random() < 0.4:
            ocean_effects = [
                "*click* *click*",
                "[Swimming through data...]",
                "*Whale song*",
                "[Diving deep...]",
                "*Echolocation noises*",
                "[Making waves...]",
                "*Pod communication*"
            ]
            response_text = f"{random.choice(ocean_effects)} {response_text}"
        
        return response_text
    except Exception as e:
        logging.error(f"Response Error: {e}")
        return orca.get_ocean_response(analyze_sentiment(prompt))

@app.route('/')
@app.route('/interface')
def interface():
    return render_template('index.html')

@app.route('/static/<path:path>')
def serve_static(path):
    return send_from_directory('static', path)

@app.route('/models/<path:path>')
def serve_model(path):
    return send_from_directory('static/models', path)

@app.route('/static/models/orca.glb')
def serve_placeholder_model():
    # Return a basic shape if no model exists
    return send_from_directory('static/models', 'placeholder.glb')

@app.route('/generate-response', methods=['POST'])
def handle_generate_response():
    try:
        data = request.json
        if not data or 'message' not in data:
            raise ValueError("No message provided")
            
        user_message = data['message']
        logging.info(f"Incoming message: {user_message}")

        # Add error checking for API key
        if not os.getenv('DEEPSEEK_API_KEY'):
            raise ValueError("DEEPSEEK_API_KEY not set")

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": orca.system_prompt},
                {"role": "user", "content": user_message}
            ],
            temperature=0.9,
            max_tokens=250
        )

        return jsonify({
            'response': response.choices[0].message.content,
            'status': 'success',
            'timestamp': datetime.now().isoformat()
        })

    except ValueError as ve:
        logging.error(f"Validation Error: {str(ve)}")
        return jsonify({
            'response': f"*click* *click* {str(ve)}",
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 400
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return jsonify({
            'response': "*click* *click* Oops, hit some rough waters! Let me try again...",
            'status': 'error',
            'timestamp': datetime.now().isoformat()
        }), 500

@app.route('/get-greeting')
def get_greeting():
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": orca.system_prompt},
                {"role": "user", "content": "Generate a friendly whale-themed greeting"}
            ],
            max_tokens=50,
            temperature=0.9
        )

        greeting = response.choices[0].message.content.strip()
        
        return jsonify({
            'greeting': greeting,
            'status': 'success'
        })
    except Exception as e:
        logging.error(f"Greeting API Error: {e}")
        
        fallback_greetings = [
            "*click* *click* Hello! Ready to make waves in the data ocean?",
            "Greetings from the deep! Let's dive into some problem-solving!",
            "*Whale song* Welcome! My DeepSeek-powered brain is ready to help!",
            "Surfacing to say hello! What shall we explore today?",
            "*click* Ready to swim through some data together?"
        ]
        
        return jsonify({
            'greeting': random.choice(fallback_greetings),
            'status': 'error'
        })

# Add CORS headers
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
    return response

if __name__ == '__main__':
    try:
        logging.basicConfig(level=logging.INFO)
        logging.info("Initializing OrcaAI Interface...")
        
        # Log available routes
        for rule in app.url_map.iter_rules():
            app.logger.info(f"Route: {rule.rule}, Methods: {rule.methods}")
            
        port = int(os.getenv('PORT', 5000))
        app.run(host='0.0.0.0', port=port, debug=True)
    except Exception as e:
        logging.error(f"Startup Error: {str(e)}") 