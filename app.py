import os
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
from datetime import datetime
from dotenv import load_dotenv 

load_dotenv() 

app = Flask(__name__)
CORS(app) 

DB_FILE = 'history_db.json'

def load_history():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data
    except json.JSONDecodeError:
        return []

def save_history(history_list):
    try:
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(history_list, f, indent=4, ensure_ascii=False)
    except IOError as e:
        print(f"Error: Gagal menyimpan riwayat ke {DB_FILE}. {e}")
# ------------------------------------

try:
    api_key = os.getenv("GEMINI_API_KEY") 
    if not api_key:
        raise ValueError("GEMINI_API_KEY tidak ditemukan di .env atau environment")
        
    genai.configure(api_key=api_key)
    
    # Ganti model yang valid
    model = genai.GenerativeModel('gemini-2.5-flash') 

except Exception as e:
    print(f"Error configuring Generative AI: {e}")
    model = None

# --- Rute untuk menyajikan halaman HTML ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/riwayat')
def history_page():
    return render_template('history.html')
# -------------------------------------------------

# --- ENDPOINT API ---

@app.route('/history', methods=['GET'])
def get_history():
    history = load_history()
    return jsonify(history)

@app.route('/generate', methods=['POST'])
def generate_content():
    if model is None:
        return jsonify({"error": "Generative AI model is not initialized."}), 500

    try:
        data = request.json
        tujuan = data.get('tujuan')
        audiens = data.get('audiens')
        produk = data.get('produk')
        usp = data.get('usp')
        platform = data.get('platform')
        nada_suara = data.get('nada_suara')
        poin_kunci = data.get('poin_kunci')
        cta = data.get('cta')

        prompt = f"""
        Anda adalah AI Generator Konten Pemasaran Cerdas.
        Tolong buatkan konten pemasaran berdasarkan detail berikut:

        1.  Tujuan Utama Konten: {tujuan}
        2.  Target Audiens: {audiens}
        3.  Produk/Layanan: {produk}
        4.  Keunggulan Utama (USP): {usp}
        5.  Platform & Jenis Konten: {platform}
        6.  Nada Suara: {nada_suara}
        7.  Poin Kunci (Wajib Ada): {poin_kunci}
        8.  Call to Action (CTA): {cta}

        Harap berikan {platform} yang relevan dan efektif berdasarkan semua informasi di atas. Berikan 3 opsi jika memungkinkan.
        """

        response = model.generate_content(prompt)
        generated_text = response.text

        new_entry = {
            "inputs": data,
            "output": generated_text,
            "timestamp": datetime.now().isoformat()
        }
        
        history = load_history()
        history.insert(0, new_entry)
        save_history(history)

        return jsonify(new_entry)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)