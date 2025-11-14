import requests
import json
import time

GEMINI_API_KEY = "AIzaSyAwa9vGoFQHmPrOm7PuH_AYh4QqRO6vWp8"
GEMINI_API_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-05-20:generateContent"

def analyze_with_gemini(ingredients, product_name):
    ingredient_names = [ing['name'] for ing in ingredients]
    system_prompt = "You are a helpful assistant that analyzes food ingredients. Provide only JSON in the specified format."
    user_query = f"""
Analyze the product '{product_name}' with ingredients: '{', '.join(ingredient_names)}'.
Rate the healthiness of the product (1-10) and each ingredient (1-10). Return JSON:
{{
  "health_rating": <float>,
  "health_stage": "<string>",
  "health_comment": "<string>",
  "ingredient_ratings": [{{"name": "<string>", "rating": <float>}}, ...]
}}
"""
    payload = {
        "contents": [{"parts": [{"text": user_query}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]},
        "generationConfig": {"responseMimeType": "application/json"}
    }
    retries = 3
    delay = 1
    for i in range(retries):
        try:
            response = requests.post(
                f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            response.raise_for_status()
            result = response.json()
            response_json = result.get('candidates', [])[0].get('content', {}).get('parts', [])[0].get('text', '{}')
            return json.loads(response_json)
        except (requests.exceptions.RequestException, json.JSONDecodeError, IndexError) as e:
            if i < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                return {"health_rating":0,"health_stage":"Error","health_comment":"Failed to generate analysis.","ingredient_ratings":[]}

def compare_products_with_gemini(products):
    product_data_str = json.dumps([{
        "name": p['name'],
        "health_rating": p.get('health_rating'),
        "ingredients": [ing['name'] for ing in p.get('ingredients',[])]
    } for p in products])
    system_prompt = "Compare food products and return JSON only."
    user_query = f"""
Analyze the products: {product_data_str}.
Return JSON:
{{
  "comparison_summary": "<string>",
  "best_product": "<string>",
  "product_breakdown": [{{"name": "<string>", "analysis": "<string>"}}]
}}
"""
    payload = {
        "contents":[{"parts":[{"text":user_query}]}],
        "systemInstruction":{"parts":[{"text":system_prompt}]},
        "generationConfig":{"responseMimeType":"application/json"}
    }
    retries=3
    delay=1
    for i in range(retries):
        try:
            response=requests.post(f"{GEMINI_API_URL}?key={GEMINI_API_KEY}",
                                   headers={'Content-Type':'application/json'},
                                   data=json.dumps(payload))
            response.raise_for_status()
            result=response.json()
            response_json=result.get('candidates',[])[0].get('content',{}).get('parts',[])[0].get('text','{}')
            return json.loads(response_json)
        except (requests.exceptions.RequestException,json.JSONDecodeError,IndexError) as e:
            if i < retries-1:
                time.sleep(delay)
                delay*=2
            else:
                return {"comparison_summary":"Failed","best_product":"N/A","product_breakdown":[]}
