from flask import Flask, render_template, request, redirect, url_for, session, flash
import csv
import os
import random
import time
from colorama import Fore, Style, init

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.jinja_env.globals.update(enumerate=enumerate)

class QuizApp:
    def __init__(self):
        self.ensure_csv_files_exist()
        self.load_users()
        self.load_quizzes()
        self.load_badges()
        self.load_notifications()
        self.admin_users = {"admin": "adminpass"}
        self.current_user = None

    def ensure_csv_files_exist(self):
        files = {
            "users.csv": ["username", "password", "score"],
            "quizzes.csv": ["category", "question", "answer", "difficulty", "hint"],
            "badges.csv": ["username", "badge"],
            "notifications.csv": ["username", "notification"],
        }

        for file_name, headers in files.items():
            if not os.path.exists(file_name):
                with open(file_name, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=headers)
                    writer.writeheader()

    def load_users(self):
        with open('users.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.users = list(reader)

    def load_quizzes(self):
        with open('quizzes.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.quizzes = list(reader)

    def load_badges(self):
        with open('badges.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.badges = list(reader)

    def load_notifications(self):
        with open('notifications.csv', 'r') as f:
            reader = csv.DictReader(f)
            self.notifications = list(reader)

    def save_users(self):
        with open('users.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "password", "score"])
            writer.writeheader()
            # Only save the required fields
            cleaned_users = []
            for user in self.users:
                cleaned_users.append({
                    "username": user["username"],
                    "password": user["password"],
                    "score": user["score"]
                })
            writer.writerows(cleaned_users)

    def save_badges(self):
        with open('badges.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "badge"])
            writer.writeheader()
            writer.writerows(self.badges)

    def save_notifications(self):
        with open('notifications.csv', 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["username", "notification"])
            writer.writeheader()
            writer.writerows(self.notifications)

    def register_user(self, username, password):
        if any(user["username"] == username for user in self.users):
            print(Fore.RED + "Username already exists! Please choose a different username.")
            return
        self.users.append({"username": username, "password": password, "score": "0"})
        self.save_users()
        print(Fore.GREEN + "Registration successful!")

    def login_user(self, username, password):
        for user in self.users:
            if user["username"].strip() == username.strip():
                if user["password"].strip() == password.strip():
                    self.current_user = user
                    print(Fore.GREEN + f"Welcome, {username}!")
                    return True
        print(Fore.RED + "Invalid username or password.")
        return False

    def view_profile(self):
        if not self.current_user:
            print(Fore.RED + "Please log in to view your profile.")
            return
        print(Fore.CYAN + f"\nProfile for {self.current_user['username']}:")
        print(f"Score: {self.current_user['score']}")
        print(Fore.YELLOW + "\nYour Badges:")
        user_badges = [badge["badge"] for badge in self.badges if badge["username"] == self.current_user["username"]]
        if user_badges:
            print(", ".join(user_badges))
        else:
            print("No badges earned yet.")
        print(Fore.MAGENTA + "\nYour Notifications:")
        user_notifications = [note["notification"] for note in self.notifications if note["username"] == self.current_user["username"]]
        if user_notifications:
            for note in user_notifications:
                print(f"- {note}")
        else:
            print("No notifications.")

    def start_quiz(self):
        if not self.current_user:
            print(Fore.RED + "Please log in to start a quiz.")
            return
        print(Fore.CYAN + "\nStarting Quiz! Answer the following questions:")
        questions = random.sample(self.quizzes, min(len(self.quizzes), 5))
        score = 0
        for question in questions:
            print(Fore.YELLOW + f"\nCategory: {question['category']} | Difficulty: {question['difficulty']}")
            print(Fore.WHITE + f"Question: {question['question']}")
            print(Fore.LIGHTBLUE_EX + f"Hint: {question['hint']}") if question["hint"] else None
            start_time = time.time()
            answer = input("Your Answer: ").strip()
            time_taken = time.time() - start_time
            if time_taken > 60:
                print(Fore.RED + "Time is up! You took too long to answer.")
                continue
            if answer.lower() == question["answer"].lower():
                print(Fore.GREEN + "Correct!")
                score += 1
            else:
                print(Fore.RED + f"Wrong! The correct answer was: {question['answer']}")
        print(Fore.CYAN + f"\nQuiz completed! Your score: {score}")
        self.update_user_score(self.current_user["username"], score)
        self.assign_badge(self.current_user["username"], score)

    def update_user_score(self, username, score):
        for user in self.users:
            if user["username"] == username:
                user["score"] = str(int(user["score"]) + score)
                break
        self.save_users()

    def assign_badge(self, username, score):
        badge = None
        if score == 9:
            badge = "Math Master"
        elif score >= 7:
            badge = "Math Enthusiast"
        elif score >= 5:
            badge = "Math Beginner"
        else:
            badge = "Math Learner"
        if badge:
            self.badges.append({"username": username, "badge": badge})
            self.save_badges()
            print(Fore.LIGHTMAGENTA_EX + f"Congratulations! You've earned the badge: {badge}")

    def admin_panel(self):
        admin_password = input("Enter admin password: ").strip()
        if admin_password != self.admin_users["admin"]:
            print(Fore.RED + "Incorrect password.")
            return
        while True:
            print(Fore.CYAN + "\nAdmin Panel:")
            print("1. View All Users")
            print("2. View All Badges")
            print("3. Add Quiz Question")
            print("4. Exit")
            choice = input(Fore.WHITE + "Enter your choice: ").strip()
            if choice == "1":
                self.view_all_users()
            elif choice == "2":
                self.view_all_badges()
            elif choice == "3":
                self.add_quiz_question()
            elif choice == "4":
                print(Fore.CYAN + "Exiting Admin Panel.")
                break
            else:
                print(Fore.RED + "Invalid choice. Try again.")

    def view_all_users(self):
        print(Fore.YELLOW + "\nRegistered Users:")
        for user in self.users:
            print(f"Username: {user['username']}, Score: {user['score']}")

    def view_all_badges(self):
        print(Fore.MAGENTA + "\nUser Badges:")
        for badge in self.badges:
            print(f"Username: {badge['username']}, Badge: {badge['badge']}")

    def add_quiz_question(self):
        category = input("Enter category: ").strip()
        question = input("Enter question: ").strip()
        answer = input("Enter answer: ").strip()
        difficulty = input("Enter difficulty (Easy/Medium/Hard): ").strip()
        hint = input("Enter hint (optional): ").strip()
        self.quizzes.append({
            "category": category,
            "question": question,
            "answer": answer,
            "difficulty": difficulty,
            "hint": hint
        })
        with open('quizzes.csv', 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=["category", "question", "answer", "difficulty", "hint"])
            writer.writerow({
                "category": category,
                "question": question,
                "answer": answer,
                "difficulty": difficulty,
                "hint": hint
            })
        print(Fore.GREEN + "Quiz question added successfully.")


quiz_app = QuizApp()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if quiz_app.login_user(username, password):
            session['username'] = username
            return redirect(url_for('dashboard'))
        return render_template('login.html', error="Invalid credentials")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        quiz_app.register_user(username, password)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    # Get current user's badges
    current_user = next((user for user in quiz_app.users if user["username"] == session["username"]), None)
    if current_user:
        current_user = dict(current_user)  # Create a copy
        current_user['badges'] = [b['badge'] for b in quiz_app.badges if b['username'] == session['username']]
    
    # Get top 10 users by score
    top_users = sorted(quiz_app.users, key=lambda x: int(x['score']), reverse=True)[:10]
    top_users_with_badges = []
    for user in top_users:
        user_copy = dict(user)
        user_copy['badges'] = [b['badge'] for b in quiz_app.badges if b['username'] == user['username']]
        top_users_with_badges.append(user_copy)
    
    return render_template('dashboard.html', user=current_user, top_users=top_users_with_badges)

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if 'username' not in session:
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        score = 0
        # Get all answers and calculate score
        for key, value in request.form.items():
            if key.startswith('answer_'):
                question_id = int(key.split('_')[1])
                if value.lower() == quiz_app.quizzes[question_id]['answer'].lower():
                    score += 1
        
        # Update user score and assign badge
        quiz_app.update_user_score(session['username'], score)
        quiz_app.assign_badge(session['username'], score)
        
        # Add a flash message for the score
        flash(f'Quiz completed! You scored {score} points!')
        return redirect(url_for('dashboard'))

    # Get 5 random questions
    questions = random.sample(quiz_app.quizzes, min(len(quiz_app.quizzes), 5))
    return render_template('quiz.html', questions=questions)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)