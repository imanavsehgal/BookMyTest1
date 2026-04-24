from flask import Flask, render_template, request, jsonify, session
import sqlite3
import math
import os
import random
import requests # Make sure to run 'pip install requests'
from datetime import datetime

app = Flask(__name__)
app.secret_key = "manav_super_secret_key"
DB_NAME = "hospital_data.db"

# Global variable to store the last sent OTP for verification

last_sent_otp = None

# --- 1. HAVERSINE DISTANCE FORMULA ---
def calculate_distance(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]):
        return float('inf') 
    
    R = 6371.0 
    lat1_rad, lon1_rad = math.radians(float(lat1)), math.radians(float(lon1))
    lat2_rad, lon2_rad = math.radians(float(lat2)), math.radians(float(lon2))
    
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

# --- 2. DATABASE INITIALIZATION & SEEDING ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Create Tables
    cursor.execute('''CREATE TABLE IF NOT EXISTS hospitals (
                        id INTEGER PRIMARY KEY, name TEXT, address TEXT, phone TEXT, lat REAL, lon REAL)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS tests (
                        id INTEGER PRIMARY KEY, hospital_id INTEGER, test_name TEXT, category TEXT, price REAL,
                        FOREIGN KEY(hospital_id) REFERENCES hospitals(id))''')
    
    cursor.execute("SELECT COUNT(*) FROM hospitals")
    if cursor.fetchone()[0] == 0:
        print("Seeding Master Database (Rohtak + Tricity)...")
        
        # 1. THE FULL 40-HOSPITAL DIRECTORY
        hospitals = [
            # --- ROHTAK (IDs 1-10) ---
            (1, 'PGIMS', 'Medical More, Rohtak', '01262-211300', 28.8833, 76.6167),
            (2, 'Noble Heart', 'Jhajjar Road, Rohtak', '01262-248781', 28.8950, 76.5800),
            (3, 'Kainos Super Speciality', 'Kheri Sadh, Rohtak', '01262-297000', 28.8700, 76.6500),
            (4, 'City Super Speciality', 'Sukhpura Chowk, Rohtak', '01262-277015', 28.9050, 76.5900),
            (5, 'Oscar Super Speciality', 'Delhi Road, Rohtak', '01262-290615', 28.8900, 76.6200),
            (6, 'Saviour Hospital', 'Mansarover Colony, Rohtak', '01262-255555', 28.8850, 76.5950),
            (7, 'Baba Mastnath', 'Asthal Bohar, Rohtak', '01262-216501', 28.8750, 76.6350),
            (8, 'Apex Diagnostics', 'Subhash Nagar, Rohtak', '01262-252111', 28.8920, 76.6000),
            (9, 'Life Care', 'Sonipat Road, Rohtak', '01262-244444', 28.9100, 76.6050),
            (10, 'Indus Public', 'Delhi Road, Rohtak', '01262-283333', 28.8930, 76.6150),

            # --- MOHALI (IDs 11-25) ---
            (11, 'Fortis Hospital', 'Sector 62, Mohali', '0172-4692222', 30.6923, 76.7363),
            (12, 'Max Super Speciality', 'Phase 6, Mohali', '0172-6652222', 30.7297, 76.7118),
            (13, 'Sohana Hospital', 'Sector 77, Mohali', '0172-2295000', 30.6861, 76.7215),
            (14, 'Ivy Hospital', 'Sector 71, Mohali', '0172-7170000', 30.7065, 76.7088),
            (15, 'Cosmo Hospital', 'Sector 62, Mohali', '0172-5095555', 30.6912, 76.7350),
            (16, 'Indus Super Speciality', 'Phase 1, Mohali', '0172-5044945', 30.7001, 76.7150),
            (17, 'Grecian Super Speciality', 'Sector 69, Mohali', '0172-4696600', 30.6945, 76.7250),
            (18, 'Livasa Hospital', 'Sector 66, Mohali', '0172-5201111', 30.6780, 76.7380),
            (19, 'Amcare Hospital', 'Zirakpur', '0176-2533000', 30.6366, 76.8183),
            (20, 'Shalby Hospital', 'Phase 9, Mohali', '0172-5056000', 30.6980, 76.7390),
            (21, 'Paras Hospital', 'Sector 22, Panchkula', '0172-5294444', 30.6865, 76.8521),
            (22, 'Park Hospital', 'Sector 47, Chandigarh', '0172-4340000', 30.7100, 76.7200),
            (23, 'Cheema Medical Complex', 'Phase 4, Mohali', '0172-2226124', 30.7150, 76.7250),
            (24, 'Silver Oaks Hospital', 'Phase 9, Mohali', '0172-2211303', 30.6950, 76.7350),
            (25, 'Shivalik Hospital', 'Sector 69, Mohali', '0172-2216666', 30.6930, 76.7280),

            # --- CHANDIGARH (IDs 26-40) ---
            (26, 'PGIMER', 'Sector 12, Chandigarh', '0172-2747585', 30.7626, 76.7766),
            (27, 'GMCH-32', 'Sector 32, Chandigarh', '0172-2601023', 30.7139, 76.7712),
            (28, 'GMSH-16', 'Sector 16, Chandigarh', '0172-2740407', 30.7483, 76.7788),
            (29, 'Mukat Hospital', 'Sector 34, Chandigarh', '0172-4344444', 30.7225, 76.7681),
            (30, 'Healing Hospital', 'Sector 34, Chandigarh', '0172-5088883', 30.7215, 76.7675),
            (31, 'Landmark Hospital', 'Sector 33, Chandigarh', '0172-2661701', 30.7145, 76.7620),
            (32, 'Santokh Hospital', 'Sector 38, Chandigarh', '0172-2691717', 30.7475, 76.7550),
            (33, 'Alchemist Hospital', 'Sector 21, Panchkula', '0172-4500000', 30.6875, 76.8500),
            (34, 'Paras Hospital Chd', 'Chandigarh', '0172-5294444', 30.6865, 76.8521),
            (35, 'Grecian Hospital Chd', 'Chandigarh', '0172-4696600', 30.6945, 76.7250),
            (36, 'Fortis Tricity', 'Chandigarh', '0172-4692222', 30.6923, 76.7363),
            (37, 'Max Tricity', 'Chandigarh', '0172-6652222', 30.7297, 76.7118),
            (38, 'Amcare Tricity', 'Chandigarh', '0176-2533000', 30.6366, 76.8183),
            (39, 'JP Hospital', 'Zirakpur', '01762-251111', 30.6420, 76.8200),
            (40, 'Mayo Hospital', 'Sector 69, Mohali', '0172-5229999', 30.6970, 76.7320)
        ]
        cursor.executemany("INSERT INTO hospitals VALUES (?, ?, ?, ?, ?, ?)", hospitals)

        # 2. GENERATE PRICES PROGRAMMATICALLY
        base_tests = [
            ('CBC', 'Pathology', 300), ('LFT', 'Pathology', 650), ('KFT', 'Pathology', 650),
            ('Lipid Profile', 'Pathology', 750), ('Thyroid Profile', 'Pathology', 900), ('HbA1c', 'Pathology', 550),
            ('Vitamin D', 'Pathology', 1500), ('Urine Routine', 'Pathology', 150), ('X-Ray Chest', 'Radiology', 450),
            ('Ultrasound', 'Radiology', 1200), ('CT Scan Brain', 'Radiology', 4200), ('MRI Brain', 'Radiology', 7000),
            ('ECG', 'Pathology', 350), ('EchoCardiography', 'Radiology', 1800), ('Full Body Checkup', 'Pathology', 3100)
        ]
        
        test_records = []
        
        # Loop through all 40 hospitals
        for h_id in range(1, 41):
            for test_name, cat, base_price in base_tests:
                
                # A. Government Tier (PGIMS, PGIMER, GMCH, GMSH)
                if h_id in [1, 26, 27, 28]: 
                    price = 10 if cat == 'Pathology' else min(base_price * 0.4, 2500)
                
                # B. Corporate Premium Tier (Fortis, Max, Ivy, Paras)
                elif h_id in [11, 12, 14, 21, 33, 34, 36, 37]:
                    price = base_price * 1.9 + 250
                    
                # C. Charitable Tier (Baba Mastnath)
                elif h_id == 7: 
                    price = base_price * 0.4
                    
                # D. Standard Private Tier (All other hospitals)
                else:
                    price = base_price * 1.4 + (h_id * 5)
                    
                # Skip heavy radiology for small clinics
                if h_id == 8 and ('Scan' in test_name or 'MRI' in test_name):
                    continue
                    
                test_records.append((h_id, test_name, cat, round(price, 2)))

        cursor.executemany("INSERT INTO tests (hospital_id, test_name, category, price) VALUES (?, ?, ?, ?)", test_records)
        conn.commit()
        print("Database Built Successfully!")
        
    conn.close()

# --- 3. ROUTES ---

@app.route('/', methods=['GET', 'POST'])
def index():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get distinct tests for the dropdown
    cursor.execute("SELECT DISTINCT test_name FROM tests ORDER BY test_name")
    test_options = [row['test_name'] for row in cursor.fetchall()]
    
    results = []
    selected_test = None

    if request.method == 'POST':
        try:
            selected_test = request.form.get('test_name')
            
            # 1. Safely grab location data and strip away any accidental spaces
            raw_lat = request.form.get('user_lat', '').strip()
            raw_lon = request.form.get('user_lon', '').strip()
            sort_preference = request.form.get('sort_by', 'distance') 
            
            # 2. Only convert to float if we actually have numbers
            user_lat = float(raw_lat) if raw_lat else None
            user_lon = float(raw_lon) if raw_lon else None
            
            cursor.execute("""
                SELECT h.name, h.address, h.phone, h.lat, h.lon, t.price, t.category 
                FROM hospitals h 
                JOIN tests t ON h.id = t.hospital_id 
                WHERE t.test_name = ?
            """, (selected_test,))
            
            raw_results = cursor.fetchall()
            
            # 3. Safe Distance Calculation
            for row in raw_results:
                if user_lat is not None and user_lon is not None:
                    dist = calculate_distance(user_lat, user_lon, row['lat'], row['lon'])
                else:
                    dist = None
                    
                results.append({
                    'name': row['name'], 'address': row['address'], 'phone': row['phone'],
                    'price': row['price'], 'category': row['category'], 'distance': dist
                })
                
            # 4. Apply Custom Sorting
            if user_lat is not None and user_lon is not None:
                if sort_preference == 'price':
                    results.sort(key=lambda x: (x['price'], x['distance']))
                else:
                    results.sort(key=lambda x: (x['distance'], x['price']))
            else:
                results.sort(key=lambda x: x['price'])
                
        except Exception as e:
            # If anything goes wrong, print it to the VS Code terminal so we can see it!
            print(f"CRASH AVOIDED: {e}")

    conn.close()
    return render_template('index.html', test_options=test_options, results=results, selected_test=selected_test)

@app.route('/book')
def book():
    hospital_name = request.args.get('hospital')
    test_name = request.args.get('test')
    price = request.args.get('price')
    return render_template('book.html', hospital=hospital_name, test=test_name, price=price)

# --- 4. OTP ROUTES ---

@app.route('/send_real_otp', methods=['POST'])
def send_real_otp():
    # 1. Grab data from the form
    phone = request.form.get('phone')
    name = request.form.get('name')
    selected_date = request.form.get('date')
    
    # 2. Set the static OTP instead of a random one
    otp_code = "1234" 
    
    # Store it in the session so the verification route can check it
    session['otp'] = otp_code
    session['chosen_date'] = selected_date
    
    # 3. Print to your terminal so you can see it working
    print(f"--- DEBUG MODE ---")
    print(f"Booking Request for: {name}")
    print(f"Phone: {phone}")
    print(f"Date: {selected_date}")
    print(f"Default OTP set to: {otp_code}")
    print(f"------------------")

    # 4. Return success immediately to the frontend
    # This will trigger the OTP box to appear in book.html
    return jsonify({"status": "success"})
        

@app.route('/verify_otp', methods=['POST'])
def verify_otp():
    user_otp = request.form.get('otp')
    
    # Retrieve the OTP we stored in the session during send_real_otp
    correct_otp = session.get('otp')
    
    if user_otp == correct_otp:
        return jsonify({"status": "verified"})
    else:
        return jsonify({"status": "wrong"})


@app.route('/confirmation')
def confirmation():
    return render_template('confirmation.html')

if __name__ == '__main__':
    # Remove init_db() if it's giving you errors
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))