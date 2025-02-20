from flask import Flask, render_template, request, jsonify, redirect, url_for
import openai
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'


# Configure your OpenAI API key (keep this secure!)
API_KEY = os.getenv("OPENAI_API_KEY")  # or assign directly
OPENAI_URI = os.getenv("AZURE_OPENAI_ENDPOINT") 
openai.api_type = "azure"
openai.api_key = API_KEY
openai.api_base = OPENAI_URI  # This should be the base URL only
openai.api_version = "2023-03-15-preview"
# Initialize SQLite database for leaderboard
DATABASE = 'leaderboard.db'

def init_db():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            rating INTEGER
        )
    ''')
    conn.commit()
    conn.close()

init_db()

def add_score(username, rating):
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('INSERT INTO leaderboard (username, rating) VALUES (?, ?)', (username, rating))
    conn.commit()
    conn.close()

def get_leaderboard():
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()
    c.execute('SELECT username, rating FROM leaderboard ORDER BY rating DESC LIMIT 10')
    results = c.fetchall()
    conn.close()
    return results

def get_joke_rating(joke):
    # Prepare the prompt for the ChatGPT API
    system_prompt = "You are a cat and your role is to rate jokes. Rate the following joke on a scale from 1 to 10. " \
                    "Provide only a number (e.g., 7) without any additional text."
    try:
        response = openai.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Joke: {joke}"}
            ],
        )
        
        rating_str = response.choices[0].message.content.strip()
        rating = int(rating_str)
        # Clamp rating between 1 and 10
        return max(1, min(10, rating))
    except Exception as e:
        print("Error in rating the joke:", e)
        return 1  # fallback rating

@app.route('/')
def index():
    # Render the main game page with the initial "sad" illustration.
    return render_template('index.html')

@app.route('/submit_joke', methods=['POST'])
def submit_joke():
    data = request.get_json()
    joke = data.get('joke')
    username = data.get('username', 'Anonymous')
    rating = get_joke_rating(joke)

    # Determine which image to use based on rating thresholds.
    if rating >= 8:
        #image = url_for('static', filename='images/laugh.png')
        mood = 'laugh'
    elif rating >= 4:
        #image = url_for('static', filename='images/smile.png')
        mood = 'smile'
    else:
        #image = url_for('static', filename='images/sad.png')
        mood = 'sad'

    # Save the score to the leaderboard
    add_score(username, rating)

    return jsonify({'rating': rating, 'mood': mood})

@app.route('/leaderboard')
def leaderboard():
    scores = get_leaderboard()
    return render_template('leaderboard.html', scores=scores)

if __name__ == '__main__':
    app.run(debug=True)
