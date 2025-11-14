from flask import Flask, request, jsonify
import json
from datetime import datetime
from dotenv import load_dotenv
import os
 # loads variables from .env

# Import database and Gemini functions
from database import get_product_by_barcode, save_user_preferences, get_user_profile, save_product_analysis
from gemini_api import analyze_with_gemini, compare_products_with_gemini

load_dotenv() 
app = Flask(__name__)

@app.route('/')
def home():
    return jsonify({"message": "NutriScan backend is running!"})
    
def analyze_ingredients(ingredients, user_id):
    user_prefs = get_user_profile(user_id)
    allergens_found=[]
    dietary_conflicts=[]
    if user_prefs:
        for allergen in user_prefs.get('allergens', []):
            if any(allergen.lower() in (ing['name'].lower() if isinstance(ing, dict) else ing.lower()) for ing in ingredients):
                allergens_found.append(allergen)
        for pref in user_prefs.get('dietary_prefs', []):
            if any(pref.lower() in (ing['name'].lower() if isinstance(ing, dict) else ing.lower()) for ing in ingredients):
                dietary_conflicts.append(pref)
    return {'allergens_found':allergens_found,'dietary_conflicts':dietary_conflicts}

@app.route('/product/<string:barcode>', methods=['GET'])
def get_product(barcode):
    product = get_product_by_barcode(barcode)
    if not product:
        return jsonify({'message':'Product not found'}),404
    user_id = request.args.get('user_id')
    if user_id:
        analysis_results=analyze_ingredients(product.get('ingredients',[]),user_id)
        product.update(analysis_results)
    else:
        product['allergens_found']=[]
        product['dietary_conflicts']=[]
    gemini_data=analyze_with_gemini(product['ingredients'],product['name'])
    product['health_rating']=gemini_data.get('health_rating',0.0)
    product['health_rating_comment']=gemini_data.get('health_comment','')
    product['health_rating_stage']=gemini_data.get('health_stage','')
    product['ingredient_ratings']=gemini_data.get('ingredient_ratings',[])
    return jsonify(product),200

@app.route('/analyze_product', methods=['POST'])
def analyze_product():
    try:
        data=request.json
        user_id,name,barcode=data.get('user_id'),data.get('name'),data.get('barcode')
        ingredients_list=data.get('ingredients',[])
        ingredients_formatted=[{'name':ing.strip()} for ing in ingredients_list if isinstance(ing,str) and ing.strip()]
        analysis_results=analyze_ingredients(ingredients_formatted,user_id)
        gemini_data=analyze_with_gemini(ingredients_formatted,name)
        product_data={
            'user_id':user_id,'name':name,'barcode':barcode,
            'ingredients':ingredients_formatted,
            'date_added':datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'),
            'health_rating':gemini_data.get('health_rating',0.0),
            'health_rating_comment':gemini_data.get('health_comment',''),
            'health_rating_stage':gemini_data.get('health_stage',''),
            'ingredient_ratings':gemini_data.get('ingredient_ratings',[]),
            **analysis_results
        }
        product_data_serializable=save_product_analysis(product_data)
        return jsonify(product_data_serializable),201
    except Exception as e:
        return jsonify({'error':'Failed to process product details','message':str(e)}),500

@app.route('/save_preferences', methods=['POST'])
def save_preferences():
    data=request.json
    user_id=data.get('user_id')
    allergens=data.get('allergens',[])
    dietary_prefs=data.get('dietary_prefs',[])
    if not user_id:
        return jsonify({'error':'User ID is required'}),400
    save_user_preferences(user_id,allergens,dietary_prefs)
    return jsonify({'message':'Preferences saved successfully'}),200

@app.route('/compare_products', methods=['POST'])
def compare_products():
    try:
        data=request.json
        barcodes=data.get('barcodes',[])
        if not barcodes or not isinstance(barcodes,list):
            return jsonify({'error':'A list of product barcodes is required.'}),400
        products_to_compare=[]
        for barcode in barcodes:
            product=get_product_by_barcode(barcode)
            if product:
                products_to_compare.append(product)
        if not products_to_compare:
            return jsonify({'error':'No products found for the provided barcodes.'}),404
        comparison_results=compare_products_with_gemini(products_to_compare)
        return jsonify(comparison_results),200
    except Exception as e:
        return jsonify({'error':'Failed to perform product comparison','message':str(e)}),500

if __name__=='__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
