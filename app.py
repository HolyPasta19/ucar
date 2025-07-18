from flask import Flask, request, jsonify
import sqlite3
from datetime import datetime, timezone



app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False
DB_PATH = 'reviews.db'

SENTIMENT_DICT = {
    'positive': [
        'хорош', 'отлич', 'прекрасн', 'замечательн', 'классн', 'крут', 
        'шикарн', 'идеальн', 'супер', 'топ', 'лучш', 'безупречн', 'бесподобн',
        'полезн', 'эффективн', 'действен', 'результат', 'качествен',
        'проверен', 'надежн', 'безопасн', 'доволен', 'рад', 'порадова', 
        'рекоменд', 'повтор', 'выбор', 'покупк','пользуюсь', 'нрав', 
        'люб', 'восторг', 'счасть', 'удивительн'
    ],
    
    'negative': [
        'плох', 'ужасн', 'отвратительн', 'кошмарн', 'разочарован', 'слаб', 
        'некачествен', 'брак', 'дефект', 'недостат', 'паршив', 'никак',
        'вредн', 'неэффективн', 'пустышк', 'обман', 'недоволен', 'неудовлетвор',
        'ненавиж','развод', 'неправд', 'ложн', 'несоответств', 'неоправдан',
        'неудобн', 'сложн', 'громоздк', 'ломает', 'тормоз',
        'глюч', 'баг', 'непонятн', 'запутан', 'непрактичн', 'нефункциональн',
        'дешев', 'крив', 'дорог', 'недостат', 'недочет', 'недоволен', 'жалоб',
         'ухудш', 'испортил', 'несоветую','сломал',
    ]
}

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA encoding = 'UTF-8'")
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            text TEXT NOT NULL,
            sentiment TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()

def analyze_sentiment(text):
    text_lower = text.lower()
    
    for word in SENTIMENT_DICT['positive']:
        if word in text_lower:
            return 'positive'
    
    for word in SENTIMENT_DICT['negative']:
        if word in text_lower:
            return 'negative'
    
    return 'neutral'

@app.route('/reviews', methods=['POST'])
def create_review():
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Поле text обязательно.'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Текст отзыва не может быть пустым.'}), 400
        
        sentiment = analyze_sentiment(text)
        created_at = datetime.now(timezone.utc).isoformat()
        
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA encoding = 'UTF-8'")
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO reviews (text, sentiment, created_at)
            VALUES (?, ?, ?)
        ''', (text, sentiment, created_at))
        
        review_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return jsonify({
            'id': review_id,
            'text': text,
            'sentiment': sentiment,
            'created_at': created_at
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/reviews', methods=['GET'])
def get_reviews():

    try:
        sentiment_filter = request.args.get('sentiment')

        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA encoding = 'UTF-8'")
        cursor = conn.cursor()
        
        if sentiment_filter:
            if sentiment_filter not in ['positive', 'negative', 'neutral']:
                return jsonify({'error': 'Неверное значение sentiment.'}), 400
            
            cursor.execute('''
                SELECT id, text, sentiment, created_at
                FROM reviews
                WHERE sentiment = ?
                ORDER BY created_at DESC
            ''', (sentiment_filter,))
        else:
            cursor.execute('''
                SELECT id, text, sentiment, created_at
                FROM reviews
                ORDER BY created_at DESC
            ''')
        
        reviews = []
        for row in cursor.fetchall():
            reviews.append({
                'id': row[0],
                'text': row[1],
                'sentiment': row[2],
                'created_at': row[3]
            })
        
        conn.close()
        
        return jsonify(reviews), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok', 'message': 'ok'}), 200

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='0.0.0.0', port=5000) 