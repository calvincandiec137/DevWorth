import os
import time
from datetime import datetime, timedelta

from cs50 import SQL
from flask import Flask, jsonify, redirect, render_template, request, session, flash
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

app = Flask(__name__)

app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

db = SQL("sqlite:///data.db")

@app.route('/')
def landing():
    if session.get("user_id") is not None:
        return redirect('/home')
    return render_template('landing.html')

@app.route('/home')
@login_required
def index():
    user_id = session['user_id']
    
    # Get user data
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    
    # Get leaderboard data
    leaderboard = db.execute("""
        SELECT u.username, l.total_experience
        FROM leaderboard l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.total_experience DESC
        LIMIT 5
    """)
    
    # Update streak logic
    current_date = time.strftime('%Y-%m-%d')
    yesterday = (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Check if user was active today
    today_activity = db.execute("""
        SELECT * FROM user_activity 
        WHERE user_id = ? AND date = ?
    """, user_id, current_date)
    
    # Check if user was active yesterday
    yesterday_activity = db.execute("""
        SELECT * FROM user_activity 
        WHERE user_id = ? AND date = ?
    """, user_id, yesterday)
    
    if today_activity:
        if yesterday_activity:
            # Increment streak if they were active yesterday
            db.execute("""
                UPDATE users 
                SET current_streak = current_streak + 1,
                    best_streak = CASE 
                        WHEN current_streak + 1 > best_streak 
                        THEN current_streak + 1 
                        ELSE best_streak 
                    END
                WHERE id = ?
            """, user_id)
        else:
            # Reset streak if they weren't active yesterday
            db.execute("UPDATE users SET current_streak = 1 WHERE id = ?", user_id)
    
    # Get updated user data after streak calculation
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    
    return render_template('home.html', user=user, leaderboard=leaderboard)

@app.route('/profile')
@login_required
def profile():
    user_id = session['user_id']
    
    # Get user data
    user = db.execute("SELECT * FROM users WHERE id = ?", user_id)[0]
    
    # Get total experience
    total_exp = db.execute("""
        SELECT COALESCE(SUM(experience), 0) as total_exp 
        FROM user_activity 
        WHERE user_id = ?
    """, user_id)[0]['total_exp']
    
    return render_template('profile.html', user=user, total_exp=total_exp)

@app.route('/get_activity_data')
@login_required
def get_activity_data():
    user_id = session['user_id']
    month = request.args.get('month')
    year = request.args.get('year')
    
    # Get available months/years
    available_dates = db.execute("""
        SELECT DISTINCT strftime('%Y-%m', date) as month_year
        FROM user_activity 
        WHERE user_id = ?
        ORDER BY month_year DESC
    """, user_id)
    
    # If month/year not specified, use most recent
    if not month or not year:
        if available_dates:
            month_year = available_dates[0]['month_year'].split('-')
            year = month_year[0]
            month = month_year[1]
    
    # Get activity data for selected month
    activity_data = db.execute("""
        SELECT date, experience 
        FROM user_activity 
        WHERE user_id = ? 
        AND strftime('%Y-%m', date) = ?
        ORDER BY date ASC
    """, user_id, f"{year}-{month}")
    
    dates = [row['date'] for row in activity_data]
    experience = [row['experience'] for row in activity_data]
    
    return jsonify({
        'dates': dates,
        'experience': experience,
        'available_dates': [d['month_year'] for d in available_dates]
    })

@app.route('/get_leaderboard')
@login_required
def get_leaderboard():
    # Get leaderboard data with more entries
    leaderboard = db.execute("""
        SELECT u.username, l.total_experience
        FROM leaderboard l
        JOIN users u ON l.user_id = u.id
        ORDER BY l.total_experience DESC
        LIMIT 10
    """)
    
    return jsonify({"status": "success", "leaderboard": leaderboard})

# Modify the update_activity route
@app.route('/update_activity', methods=['POST'])
@login_required
def update_activity():
    user_id = session['user_id']
    current_time = time.time()
    login_time = session.get('login_time')

    if login_time:
        time_spent = int(current_time - login_time)
        # Calculate experience (10 XP per minute)
        experience = (time_spent // 60) * 10

        current_date = time.strftime('%Y-%m-%d')

        try:
            # Update user_activity
            db.execute("""
                INSERT INTO user_activity (user_id, date, time_spent, experience)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id, date) 
                DO UPDATE SET 
                time_spent = time_spent + ?,
                experience = experience + ?
            """, user_id, current_date, time_spent, experience, time_spent, experience)
            
            # Update leaderboard with fresh total
            total_exp = db.execute("""
                SELECT COALESCE(SUM(experience), 0) as total_exp 
                FROM user_activity 
                WHERE user_id = ?
            """, user_id)[0]['total_exp']
            
            db.execute("""
                INSERT INTO leaderboard (user_id, total_experience)
                VALUES (?, ?)
                ON CONFLICT(user_id) 
                DO UPDATE SET total_experience = ?
            """, user_id, total_exp, total_exp)
            
            # Reset login time to current time
            session['login_time'] = current_time
            
            return jsonify({
                "status": "success",
                "experience": total_exp
            })
            
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "error", "message": "No login time found"}), 400

@app.route('/login', methods=['GET', 'POST'])
def login():
    
    #redirect if already logged in
    if session.get("user_id") is not None:
        return redirect('/home')

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        nameErr = None
        passErr = None

        if not username:
            nameErr = 'Username required!'
        elif not password:
            passErr = 'Password required!'
        else:
            user = db.execute("SELECT * FROM users WHERE username = ?", username)

            if len(user) == 0:
                nameErr = 'Invalid username'

            if len(user) != 1 or not check_password_hash(user[0]['password'], password):
                passErr = 'Invalid Password'
            else:
                session['user_id'] = user[0]['id']
                session['login_time'] = time.time()
                return redirect('/home')

        return render_template('login.html', nameErr=nameErr, passErr=passErr)

    else:
        return render_template('login.html')

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect('/login')

@app.route('/signup', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password1 = request.form['password1']
        password2 = request.form['password2']

        user = db.execute("SELECT * FROM users WHERE username = ?", username)

        nameErr = None
        passErr = None
        pass2Err = None
        passMatch = None

        if len(user) > 0:
            nameErr = 'User already exists'

        elif not username:
            nameErr = 'Username required!'

        elif not password1:
            passErr = 'Password required!'

        elif not password2:
            pass2Err = 'Confirm Password required!'

        elif password1 != password2:
            passMatch = 'Passwords do not match!'

        else:
            hash = generate_password_hash(password1)

            db.execute("INSERT INTO users (username, password) VALUES(?, ?)", username, hash)

            return redirect('/login')

        return render_template('signup.html', nameErr = nameErr,
        passErr = passErr,
        pass2Err = pass2Err,
        passMatch = passMatch)

    else:
        return render_template('signup.html')
