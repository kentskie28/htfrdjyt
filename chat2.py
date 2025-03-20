import json
import pickle
import numpy as np
from nltk_util import tokenize

with open("nb_model.pkl", "rb") as f:
    model, vectorizer, label_encoder = pickle.load(f)

with open('data/intents.json', 'r', encoding='utf-8') as f:
    intents = json.load(f)

def predict_intent(text):
    X = vectorizer.transform([text])
    probabilities = model.predict_proba(X)[0]
    tag_index = np.argmax(probabilities) 
    tag = label_encoder.inverse_transform([tag_index])[0]  
    confidence = probabilities[tag_index] 
    
    for intent in intents['intents']:
        if intent['tag'] == tag:
            return tag, np.random.choice(intent['responses']), confidence, probabilities

    return "unknown", "Sorry, I didn't understand that.", 0.0, probabilities

while True:
    user_input = input("You: ")
    if user_input.lower() in ["quit", "exit"]:
        break

    intent, response, confidence, probabilities = predict_intent(user_input)
    
    print(f"Bot ({intent}) [Confidence: {confidence:.2f}]: {response}")
    
    print("\n--- Intent Probabilities ---")
    for tag, prob in zip(label_encoder.classes_, probabilities):
        print(f"{tag}: {prob:.4f}")
    print("----------------------------\n")
