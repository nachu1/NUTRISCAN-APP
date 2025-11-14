import mysql.connector
import json
from mysql.connector import Error

# Configure SingleStore/MySQL connection
DB_CONFIG = {
    'host': 'svc-3482219c-a389-4079-b18b-d50662524e8a-shared-dml.aws-virginia-6.svc.singlestore.com',
    'user': 'mohammad-f295d',
    'password': 'G0ReK}M3z}xj1v[t8q);{k',
    'database': 'db_mohammad_0edbf',
    'port': 3333
}

def get_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def get_product_by_barcode(barcode):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM products WHERE barcode=%s", (barcode,))
    product = cursor.fetchone()
    if product:
        # Convert JSON strings back to Python objects
        for key in ['ingredients', 'allergens_found', 'dietary_conflicts', 'ingredient_ratings']:
            if product.get(key):
                product[key] = json.loads(product[key])
            else:
                product[key] = []
    cursor.close()
    conn.close()
    return product

def save_user_preferences(user_id, allergens, dietary_prefs):
    conn = get_connection()
    if not conn:
        return
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO user_profiles (user_id, allergens, dietary_prefs)
        VALUES (%s, %s, %s)
        ON DUPLICATE KEY UPDATE allergens=%s, dietary_prefs=%s
    """, (user_id, json.dumps(allergens), json.dumps(dietary_prefs),
          json.dumps(allergens), json.dumps(dietary_prefs)))
    conn.commit()
    cursor.close()
    conn.close()

def get_user_profile(user_id):
    conn = get_connection()
    if not conn:
        return None
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM user_profiles WHERE user_id=%s", (user_id,))
    user = cursor.fetchone()
    if user:
        user['allergens'] = json.loads(user.get('allergens', '[]'))
        user['dietary_prefs'] = json.loads(user.get('dietary_prefs', '[]'))
    cursor.close()
    conn.close()
    return user

def save_product_analysis(product_data):
    conn = get_connection()
    if not conn:
        return product_data
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO products
        (user_id, name, barcode, ingredients, date_added, health_rating, health_rating_comment, health_rating_stage,
         ingredient_ratings, allergens_found, dietary_conflicts)
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
    """, (
        product_data['user_id'],
        product_data['name'],
        product_data['barcode'],
        json.dumps(product_data['ingredients']),
        product_data['date_added'],
        product_data['health_rating'],
        product_data['health_rating_comment'],
        product_data['health_rating_stage'],
        json.dumps(product_data['ingredient_ratings']),
        json.dumps(product_data['allergens_found']),
        json.dumps(product_data['dietary_conflicts'])
    ))
    conn.commit()
    cursor.close()
    conn.close()
    return product_data
