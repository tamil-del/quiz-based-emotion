from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file

# Flask-Mail is an optional dependency; if it's not installed we
# fall back to a no-op so that the rest of the app continues to work.
try:
    from flask_mail import Mail, Message
except ImportError:
    Mail = None
    Message = None

import sqlite3
import json
import os
from datetime import datetime
import random
import base64

# in-memory list of sample questions with id
QUESTIONS = []

def create_sample_questions():
    global QUESTIONS
    sample = [
        ('Which activity makes you feel most joyful?', 'Listening to music', 'Watching comedy', 'Eating favorite food', 'Meeting friends', 3, 'happy', 10),
        ('What color represents happiness for you?', 'Blue', 'Yellow', 'Red', 'Green', 2, 'happy', 10),
        ('What is the best way to celebrate success?', 'Party with friends', 'Buy yourself a gift', 'Relax at home', 'Plan next goal', 1, 'happy', 10),
        ('What helps you when you are feeling down?', 'Sleeping', 'Talking to someone', 'Watching TV', 'Exercise', 2, 'sad', 10),
        ('Which music genre comforts you when sad?', 'Classical', 'Pop', 'Rock', 'Instrumental', 4, 'sad', 10),
        ('What activity can lift your mood?', 'Going for a walk', 'Eating sweets', 'Shopping', 'Gaming', 1, 'sad', 10),
        ('What helps control anger effectively?', 'Deep breathing', 'Shouting', 'Breaking things', 'Ignoring', 1, 'angry', 10),
        ('Which technique is best for anger management?', 'Counting to 10', 'Venting online', 'Physical exercise', 'Listening to music', 1, 'angry', 10),
        ('What color is often associated with anger?', 'Blue', 'Green', 'Red', 'Yellow', 3, 'angry', 10),
        ('What describes a neutral mood best?', 'Calm and balanced', 'Bored', 'Tired', 'Confused', 1, 'neutral', 10),
        ('What do you prefer in a neutral mood?', 'Quiet time alone', 'Social gathering', 'Adventure', 'Learning', 1, 'neutral', 10),
        ('Which weather matches neutral mood?', 'Sunny', 'Rainy', 'Partly cloudy', 'Stormy', 3, 'neutral', 10),
        ('What excites you the most?', 'New adventures', 'Achieving goals', 'Surprises', 'Learning new things', 1, 'excited', 10),
        ('How do you express excitement?', 'Jumping', 'Smiling', 'Talking fast', 'All of the above', 4, 'excited', 10),
        ('What triggers excitement easily?', 'Unexpected gifts', 'Travel plans', 'Meeting idols', 'All of these', 4, 'excited', 10)
    ]
    QUESTIONS = []
    for idx, q in enumerate(sample, start=1):
        QUESTIONS.append({
            'id': idx,
            'question': q[0],
            'options': [q[1], q[2], q[3], q[4]],
            'correct_answer': q[5],
            'emotion': q[6],
            'points': q[7]
        })

create_sample_questions()

app = Flask(__name__)
app.secret_key = 'emotion-quiz-secret-key-2024'

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Change this
app.config['MAIL_PASSWORD'] = 'your-password'  # Change this
mail = Mail(app)

# SQLite helper functions
DATABASE = 'quiz.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS results (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        emotion TEXT NOT NULL,
        score INTEGER NOT NULL,
        total_questions INTEGER NOT NULL,
        correct_answers INTEGER NOT NULL,
        time_taken INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        rating INTEGER NOT NULL,
        comments TEXT,
        category TEXT,
        emoji_reaction TEXT,
        camera_experience TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )""")
    # ensure category column exists for older databases
    try:
        cursor.execute("ALTER TABLE feedback ADD COLUMN category TEXT")
    except sqlite3.OperationalError:
        # column already exists
        pass
    conn.commit()
    conn.close()



@app.route('/')
def home():
    return render_template('home.html')

@app.route('/static/manifest.json')
def serve_manifest():
    return send_file('static/manifest.json', mimetype='application/manifest+json')

@app.route('/static/service-worker.js')
def serve_service_worker():
    return send_file('static/service-worker.js', mimetype='application/javascript')

@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    email = request.form['email']
    conn = get_db()
    try:
        cur = conn.execute("SELECT id, username, email FROM users WHERE username=? OR email=?", (username, email))
        existing = cur.fetchone()
        if existing:
            return jsonify({'success': False,'message': 'Username or email already exists!'})
        cur = conn.execute("INSERT INTO users(username,email) VALUES(?,?)", (username, email))
        conn.commit()
        user_id = cur.lastrowid
        session['user_id'] = user_id
        session['username'] = username
        session['email'] = email
        session.modified = True
        return jsonify({'success': True,'message': 'Registration successful!','user_id': user_id,'username': username})
    except sqlite3.IntegrityError as e:
        return jsonify({'success': False, 'message': 'Username or email already exists!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Registration failed: {str(e)}'})
    finally:
        conn.close()

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    conn = get_db()
    cur = conn.execute("SELECT id, username, email FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    if user:
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['email'] = user['email']
        session.modified = True
        return jsonify({'success': True,'message': 'Login successful!','username': user['username']})
    else:
        return jsonify({'success': False,'message': 'User not found! Please register first.'})

@app.route('/detect_emotion', methods=['POST'])
def detect_emotion():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    
    # Check if image file is provided
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image provided'})
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'success': False, 'message': 'No file selected'})
    
    try:
        # Read the image file
        image_data = file.read()
        
        # For demo purposes, randomly select an emotion
        # In a real project, you would use a deep learning model for emotion detection
        emotions = ['happy', 'sad', 'angry', 'neutral', 'excited']
        detected_emotion = random.choice(emotions)
        confidence = random.uniform(0.75, 0.99)
        
        # Store emotion in session
        session['current_emotion'] = detected_emotion
        
        return jsonify({
            'success': True,
            'emotion': detected_emotion,
            'confidence': confidence,
            'message': f'Emotion detected: {detected_emotion}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'Error processing image: {str(e)}'
        })

@app.route('/get_questions/<emotion>')
def get_questions(emotion):
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    # filter by emotion
    filtered = [q for q in QUESTIONS if q['emotion'] == emotion]
    if not filtered:
        filtered = QUESTIONS
    sampled = random.sample(filtered, min(5, len(filtered)))
    return jsonify({'success': True, 'questions': sampled})

@app.route('/start_quiz')
def start_quiz():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    emotion = request.args.get('emotion', session.get('current_emotion', 'happy'))
    session['current_emotion'] = emotion
    
    return render_template('quiz.html',
                         username=session['username'],
                         emotion=emotion)

@app.route('/submit_quiz', methods=['POST'])
def submit_quiz():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    data = request.json
    answers = data.get('answers', [])
    time_taken = data.get('time_taken', 0)
    score = 0
    correct_count = 0
    total_questions = len(answers)
    # score using QUESTIONS list
    qdict = {q['id']: q for q in QUESTIONS}
    for answer in answers:
        qid = answer['question_id']
        sel = answer['selected_option']
        q = qdict.get(qid)
        if q and sel == q['correct_answer']:
            score += q['points']
            correct_count += 1
    # save to sqlite
    conn = get_db()
    cur = conn.execute(
        """INSERT INTO results(user_id, username, emotion, score, total_questions, correct_answers, time_taken)
           VALUES(?,?,?,?,?,?,?)""",
        (session['user_id'], session['username'], session.get('current_emotion','neutral'), score, total_questions, correct_count, time_taken)
    )
    conn.commit()
    result_id = cur.lastrowid
    # calculate rank by querying all results
    cur = conn.execute("SELECT score, time_taken FROM results")
    rows = cur.fetchall()
    rank = 1
    for r in rows:
        if r['score'] > score or (r['score'] == score and r['time_taken'] < time_taken):
            rank += 1
    conn.close()
    session['last_score'] = score
    session['last_correct'] = correct_count
    session['last_total'] = total_questions
    session['last_result_id'] = result_id
    return jsonify({'success': True,'score': score,'correct': correct_count,'total': total_questions,'rank': rank,'result_id': result_id})

@app.route('/result')
def result():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    
    return render_template('result.html',
                         username=session['username'],
                         score=session.get('last_score', 0),
                         correct=session.get('last_correct', 0),
                         total=session.get('last_total', 0),
                         emotion=session.get('current_emotion', 'neutral'))

@app.route('/leaderboard')
def leaderboard():
    conn = get_db()
    cur = conn.execute("SELECT user_id, username, score, correct_answers, total_questions FROM results")
    rows = cur.fetchall()
    conn.close()
    total_players = len(set(r['user_id'] for r in rows))
    avg_score = sum(r['score'] for r in rows) / len(rows) if rows else 0
    # accumulate per-player stats
    player_best = {}
    for r in rows:
        uid = r['user_id']
        if uid not in player_best:
            player_best[uid] = {
                'username': r['username'],
                'best_score': r['score'],
                'total_score': r['score'],
                'total_quizzes': 1,
                'correct_answers': r['correct_answers'],
                'total_questions': r['total_questions']
            }
        else:
            stats = player_best[uid]
            stats['best_score'] = max(stats['best_score'], r['score'])
            stats['total_score'] += r['score']
            stats['total_quizzes'] += 1
            stats['correct_answers'] += r['correct_answers']
            stats['total_questions'] += r['total_questions']
    leaderboard = []
    for uid, stats in player_best.items():
        acc = (stats['correct_answers'] / stats['total_questions'] * 100) if stats['total_questions'] else 0
        leaderboard.append({
            'user_id': uid,
            'username': stats['username'],
            'best_score': stats['best_score'],
            'total_score': stats['total_score'],
            'accuracy': round(acc,1),
            'quiz_count': stats['total_quizzes'],
            'is_current_user': session.get('user_id') == uid
        })
    leaderboard.sort(key=lambda x: (x['best_score'], x['total_score']), reverse=True)
    top_players = leaderboard[:3]
    your_rank = 'N/A'; your_best_score = 0
    your_stats = None
    if 'user_id' in session:
        uid = session['user_id']
        for idx,p in enumerate(leaderboard,1):
            if p['user_id'] == uid:
                your_rank = idx
                your_best_score = p['best_score']
                break
        # compute user stats from player_best dict
        stats = player_best.get(uid)
        if stats:
            total_quizzes = stats['total_quizzes']
            best_score = stats['best_score']
            avg_score_user = stats['total_score'] / total_quizzes if total_quizzes else 0
            best_accuracy = (stats['correct_answers'] / stats['total_questions'] * 100) if stats['total_questions'] else 0
            total_points = stats['total_score']
            your_stats = {
                'total_quizzes': total_quizzes,
                'best_score': best_score,
                'avg_score': round(avg_score_user,1),
                'best_accuracy': round(best_accuracy,1),
                'total_points': total_points
            }
    return render_template('leaderboard.html',
                         total_players=total_players,
                         avg_score=round(avg_score,1),
                         your_rank=your_rank,
                         your_best_score=your_best_score,
                         top_players=top_players,
                         leaderboard=leaderboard,
                         your_stats=your_stats,
                         username=session.get('username','Guest'))

@app.route('/certificate')
def certificate():
    if 'user_id' not in session or 'last_score' not in session:
        return redirect(url_for('home'))
    
    certificate_data = {
        'username': session['username'],
        'score': session['last_score'],
        'correct': session['last_correct'],
        'total': session['last_total'],
        'emotion': session.get('current_emotion', 'neutral'),
        'date': datetime.now().strftime('%B %d, %Y'),
        'certificate_id': f"EBQ{datetime.now().strftime('%Y%m%d')}{session.get('last_result_id', 0):04d}"
    }
    
    return render_template('certificate.html', **certificate_data)

@app.route('/feedback')
def feedback():
    if 'user_id' not in session:
        return redirect(url_for('home'))
    conn = get_db()
    cur = conn.execute("SELECT user_id, rating FROM feedback")
    rows = cur.fetchall()
    conn.close()
    total_feedback = len(rows)
    avg_rating = sum(r['rating'] for r in rows) / total_feedback if total_feedback > 0 else 0
    satisfied = sum(1 for r in rows if r['rating'] >= 4)
    satisfaction_rate = (satisfied / total_feedback * 100) if total_feedback > 0 else 0
    unique_users = len(set(r['user_id'] for r in rows))
    # compute rating distribution counts
    rating_counts = {i:0 for i in range(1,6)}
    for r in rows:
        rating_counts[r['rating']] = rating_counts.get(r['rating'], 0) + 1
    max_feedback_count = max(rating_counts.values()) if rating_counts else 0
    # prepare recent_feedback list of dicts
    recent = []
    conn = get_db()
    cur = conn.execute("SELECT username, rating, comments, emoji_reaction, camera_experience, created_at FROM feedback ORDER BY created_at DESC LIMIT 6")
    recrows = cur.fetchall()
    conn.close()
    for r in recrows:
        recent.append({
            'username': r['username'],
            'rating': r['rating'],
            'feedback': r['comments'],
            'emotion': r['emoji_reaction'] if 'emoji_reaction' in r.keys() else '',
            'category': r['category'] if 'category' in r.keys() else '',
            'date': r['created_at']
        })
    category_counts = {}
    return render_template('feedback.html',
                         username=session['username'],
                         total_feedback=total_feedback,
                         avg_rating=round(avg_rating,1),
                         satisfaction_rate=round(satisfaction_rate,0),
                         unique_users=unique_users,
                         recent_feedback=recent,
                         rating_counts=rating_counts,
                         max_feedback_count=max_feedback_count,
                         category_counts=category_counts)

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    data = request.json
    rating = data.get('rating')
    comments = data.get('comments', '')
    emoji_reaction = data.get('emoji_reaction', '')
    camera_experience = data.get('camera_experience', '')
    conn = get_db()
    category = data.get('category','')
    conn.execute(
        """INSERT INTO feedback(user_id, username, rating, comments, category, emoji_reaction, camera_experience)
           VALUES(?,?,?,?,?,?,?)""",
        (session['user_id'], session['username'], rating, comments, category, emoji_reaction, camera_experience)
    )
    conn.commit()
    conn.close()
    return jsonify({'success': True,'message': 'Thank you for your feedback!'})

@app.route('/get_feedback_stats')
def get_feedback_stats():
    conn = get_db()
    cur = conn.execute("SELECT rating, camera_experience FROM feedback")
    rows = cur.fetchall()
    conn.close()
    total = len(rows)
    avg_rating = sum(r['rating'] for r in rows) / total if total > 0 else 0
    camera_users = sum(1 for r in rows if r['camera_experience'])
    rating_counts = {}
    for r in rows:
        rating_counts[r['rating']] = rating_counts.get(r['rating'], 0) + 1
    rating_dist = [{'rating': r, 'count': c} for r, c in sorted(rating_counts.items())]
    return jsonify({'success': True,'total': total,'avg_rating': round(avg_rating,1),'camera_users': camera_users,'rating_distribution': rating_dist})

@app.route('/send_certificate_email', methods=['POST'])
def send_certificate_email():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    
    data = request.json
    email = data.get('email', session.get('email'))
    
    if not email:
        return jsonify({'success': False, 'message': 'No email provided!'})
    
    if Mail is None:
        # Flask-Mail not installed or disabled; skip email send
        return jsonify({'success': False, 'message': 'Email support not available'})
    try:
        msg = Message('Your Emotion Quiz Certificate',
                      sender='your-email@gmail.com',
                      recipients=[email])
        
        msg.html = f'''
        <h2>Emotion Quiz Certificate</h2>
        <p>Congratulations {session['username']}!</p>
        <p>You scored {session.get('last_score', 0)} points in the {session.get('current_emotion', 'neutral')} emotion quiz.</p>
        <p>Keep up the great work!</p>
        '''
        
        mail.send(msg)
        return jsonify({'success': True, 'message': 'Certificate sent to email!'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'Failed to send email: {str(e)}'})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))

import os

if __name__ == '__main__':
    init_db()
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)