from flask import Flask, render_template, request, redirect, url_for, session, jsonify, send_file
from flask_mail import Mail, Message
from models import db, User, Question, Result, Feedback
import json
import os
from datetime import datetime
import random
import base64

app = Flask(__name__)
app.secret_key = 'emotion-quiz-secret-key-2024'

# Session configuration
app.config['SESSION_TYPE'] = 'filesystem'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 hour

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Mail configuration
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Change this
app.config['MAIL_PASSWORD'] = 'your-password'  # Change this
mail = Mail(app)

# Initialize database and insert sample questions
def init_db():
    with app.app_context():
        db.create_all()
        
        # Check if questions already exist
        if Question.query.first() is None:
            insert_sample_questions()
            db.session.commit()

def insert_sample_questions():
    sample_questions = [
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
    
    for question_data in sample_questions:
        question = Question(
            question=question_data[0],
            option1=question_data[1],
            option2=question_data[2],
            option3=question_data[3],
            option4=question_data[4],
            correct_answer=question_data[5],
            emotion=question_data[6],
            points=question_data[7]
        )
        db.session.add(question)


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
    
    try:
        # Check if user already exists
        existing_user = User.query.filter((User.username == username) | (User.email == email)).first()
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Username or email already exists!'
            })
        
        user = User(username=username, email=email)
        db.session.add(user)
        db.session.commit()
        
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Registration successful!',
            'user_id': user.id,
            'username': user.username
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Registration failed: {str(e)}'
        })

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    
    user = User.query.filter_by(username=username).first()
    
    if user:
        session['user_id'] = user.id
        session['username'] = user.username
        session['email'] = user.email
        session.modified = True
        
        return jsonify({
            'success': True,
            'message': 'Login successful!',
            'username': user.username
        })
    else:
        return jsonify({
            'success': False,
            'message': 'User not found! Please register first.'
        })

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
    
    # Get 5 random questions for the emotion
    questions = Question.query.filter_by(emotion=emotion).order_by(db.func.random()).limit(5).all()
    
    if not questions:
        # If no questions for this emotion, get any 5 questions
        questions = Question.query.order_by(db.func.random()).limit(5).all()
    
    questions_list = [q.to_dict() for q in questions]
    
    return jsonify({'success': True, 'questions': questions_list})

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
    
    for answer in answers:
        question_id = answer['question_id']
        selected_option = answer['selected_option']
        
        question = Question.query.get(question_id)
        
        if question and selected_option == question.correct_answer:
            score += question.points
            correct_count += 1
    
    # Create and save result
    result = Result(
        user_id=session['user_id'],
        username=session['username'],
        emotion=session.get('current_emotion', 'neutral'),
        score=score,
        total_questions=total_questions,
        correct_answers=correct_count,
        time_taken=time_taken
    )
    
    db.session.add(result)
    db.session.commit()
    
    # Calculate rank
    rank = Result.query.filter(
        (Result.score > score) | ((Result.score == score) & (Result.time_taken < time_taken))
    ).count() + 1
    
    session['last_score'] = score
    session['last_correct'] = correct_count
    session['last_total'] = total_questions
    session['last_result_id'] = result.id
    
    return jsonify({
        'success': True,
        'score': score,
        'correct': correct_count,
        'total': total_questions,
        'rank': rank,
        'result_id': result.id
    })

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
    # Get top 10 scores
    top_scores_raw = db.session.query(Result).order_by(
        Result.score.desc(), 
        Result.time_taken.asc()
    ).limit(10).all()
    
    # Convert to dicts and format dates
    top_scores = []
    for result in top_scores_raw:
        score_dict = result.to_dict()
        score_dict['created_at_formatted'] = result.created_at.strftime('%Y-%m-%d') if result.created_at else 'N/A'
        top_scores.append(result)  # Keep original object for template access
    
    user_best = None
    if 'user_id' in session:
        user_results = Result.query.filter_by(user_id=session['user_id']).all()
        if user_results:
            user_best = {
                'best_score': max(r.score for r in user_results),
                'total_quizzes': len(user_results),
                'emotions_played': ', '.join(set(r.emotion for r in user_results))
            }
    
    return render_template('leaderboard.html',
                         top_scores=top_scores,
                         user_best=user_best,
                         username=session.get('username', 'Guest'))

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
    return render_template('feedback.html', username=session['username'])

@app.route('/submit_feedback', methods=['POST'])
def submit_feedback():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    
    data = request.json
    rating = data.get('rating')
    comments = data.get('comments', '')
    emoji_reaction = data.get('emoji_reaction', '')
    camera_experience = data.get('camera_experience', '')
    
    feedback_obj = Feedback(
        user_id=session['user_id'],
        username=session['username'],
        rating=rating,
        comments=comments,
        emoji_reaction=emoji_reaction,
        camera_experience=camera_experience
    )
    
    db.session.add(feedback_obj)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'Thank you for your feedback!'
    })

@app.route('/get_feedback_stats')
def get_feedback_stats():
    all_feedback = Feedback.query.all()
    
    total = len(all_feedback)
    avg_rating = sum(f.rating for f in all_feedback) / total if total > 0 else 0
    camera_users = sum(1 for f in all_feedback if f.camera_experience)
    
    # Get rating distribution
    rating_counts = {}
    for f in all_feedback:
        rating_counts[f.rating] = rating_counts.get(f.rating, 0) + 1
    
    rating_dist = [{'rating': r, 'count': c} for r, c in sorted(rating_counts.items())]
    
    return jsonify({
        'success': True,
        'total': total,
        'avg_rating': round(avg_rating, 1),
        'camera_users': camera_users,
        'rating_distribution': rating_dist
    })

@app.route('/send_certificate_email', methods=['POST'])
def send_certificate_email():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Please login first!'})
    
    data = request.json
    email = data.get('email', session.get('email'))
    
    if not email:
        return jsonify({'success': False, 'message': 'No email provided!'})
    
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

if __name__ == '__main__':
    init_db()
    app.run(debug=False, port=5000, host='127.0.0.1')