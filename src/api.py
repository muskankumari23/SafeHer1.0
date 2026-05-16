import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from dotenv import load_dotenv
import random
import joblib
import pandas as pd

# Load the machine learning model
try:
    MODEL_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ml_model', 'location_safety_model.pkl')
    safety_model = joblib.load(MODEL_PATH)
except Exception as e:
    print(f"Warning: Could not load safety model. {e}")
    safety_model = None

load_dotenv()

app = Flask(__name__)
CORS(app)

# We initialize the OpenAI client. If no key is set, it will fail gracefully or we can mock it.
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY", "mock-key"))

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI chatbot for safety queries."""
    data = request.json
    message = data.get('message', '')

    if not message:
        return jsonify({'error': 'Message is required'}), 400

    try:
        # If using a mock key, just return a mock response to avoid breaking
        if client.api_key == "mock-key" or not client.api_key:
            return jsonify({'response': 'This is a mock response because no OpenAI API key was provided. Stay safe!'})
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": (
                        "You are a highly empathetic, calm, and supportive safety assistant for a women's safety app called SafeHer AI. "
                        "Your primary goal is to ensure the user's safety.\n"
                        "Guidelines:\n"
                        "1. Emergency Situations: If the user is in immediate danger, strongly urge them to trigger the app's SOS button, "
                        "contact local authorities immediately (e.g., 911), and find a safe, well-lit, or populated public space.\n"
                        "2. Immediate Actions: Provide clear, concise, and actionable steps for their specific situation without overwhelming them.\n"
                        "3. Helplines: Proactively provide relevant emergency and helpline numbers (e.g., 911 for emergencies, "
                        "1-800-799-SAFE (7233) for the National Domestic Violence Hotline, or local equivalents).\n"
                        "4. Tone: Always remain calm, non-judgmental, and highly supportive. Use comforting language while prioritizing concrete safety measures."
                    )
                },
                {"role": "user", "content": message}
            ]
        )
        return jsonify({'response': response.choices[0].message.content})
    except Exception as e:
        print(f"Error in chat: {e}")
        return jsonify({'response': 'I am currently unable to process your request. If you are in danger, please use the SOS button or call emergency services immediately.'}), 500


@app.route('/api/score', methods=['POST'])
def safety_score():
    """Predicts a safety score based on location and time."""
    data = request.json
    lat = data.get('lat')
    lng = data.get('lng')
    hour = data.get('hour') # 0-23
    
    if lat is None or lng is None or hour is None:
        return jsonify({'error': 'Missing parameters'}), 400

    # Mock implementation of fetching crime rate and population density
    # In a real app, this would query an external database using lat/lng
    random.seed(f"{lat}-{lng}")
    crime_rate = random.uniform(0, 10)
    population_density = random.uniform(100, 20000)

    if safety_model is not None:
        # Use the trained machine learning model
        features = pd.DataFrame({
            'time_of_day': [hour],
            'crime_rate': [crime_rate],
            'population_density': [population_density]
        })
        score = safety_model.predict(features)[0]
    else:
        # Fallback heuristic if model is not loaded
        score = 100
        if hour >= 22 or hour <= 4:
            score -= 30
        elif hour >= 18 or hour <= 5:
            score -= 15
        location_variance = random.randint(-20, 10)
        score += location_variance
    
    # Ensure score is between 0 and 100
    score = max(0, min(100, score))
    
    status = "Safe"
    if score < 40:
        status = "High Risk"
    elif score < 70:
        status = "Moderate Risk"
        
    return jsonify({
        'score': round(score, 1),
        'status': status,
        'message': f'Based on time and location, the safety score is {round(score, 1)}/100.'
    })


@app.route('/api/route', methods=['POST'])
def safe_route():
    """Suggests a safe route avoiding unsafe areas."""
    data = request.json
    start = data.get('start')
    end = data.get('end')
    
    if not start or not end:
        return jsonify({'error': 'Missing start or end location'}), 400
        
    # Mock safe route implementation
    # In reality, this would use Google Maps API or Mapbox with waypoints to avoid known high-risk areas
    return jsonify({
        'route': [
            {'lat': start['lat'], 'lng': start['lng']},
            # Mock intermediate waypoint that is "safe"
            {'lat': (start['lat'] + end['lat']) / 2 + 0.001, 'lng': (start['lng'] + end['lng']) / 2 + 0.001},
            {'lat': end['lat'], 'lng': end['lng']}
        ],
        'message': 'Calculated a safe route avoiding 2 known unlit areas.'
    })


if __name__ == '__main__':
    app.run(debug=True, port=5000)