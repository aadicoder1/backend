from transformers import AutoModelForSeq2SeqLM, AutoTokenizer
import torch
import requests
import json

# Load local LLM
tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")

RASA_API = "http://127.0.0.1:5005/webhooks/rest/webhook"

def get_rasa_response(message):
    try:
        resp = requests.post(RASA_API, json={"sender": "user", "message": message})
        data = resp.json()
        if data:
            return " ".join([d.get("text","") for d in data])
    except:
        pass
    return None

def get_llm_response(message):
    inputs = tokenizer("Answer: " + message, return_tensors="pt")
    outputs = model.generate(**inputs, max_new_tokens=100)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

def chatbot_response(message):
    # 1️⃣ Try Rasa first
    rasa_reply = get_rasa_response(message)
    if rasa_reply:
        return rasa_reply
    # 2️⃣ Fallback to local LLM
    return get_llm_response(message)

# Example
while True:
    msg = input("You: ")
    if msg.lower() in ["exit", "quit"]:
        break
    print("Ameya:", chatbot_response(msg))
