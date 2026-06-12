# LearnTrack 🚀
### A Personalized Learning Tracker & Gamified Study Assistant

LearnTrack is a production-ready, responsive Python Flask web application designed to help users organize, track, and optimize their educational journeys. With a sleek dark-themed navigation structure, glassmorphic UI elements, study streaks, achievement badges, and interest-based study recommendations, it provides a premium Learning Management System (LMS) experience.

---

## 🌟 Key Features

1. **Secure Authentication**: Register and log in with password hashing (Bcrypt), session persistence, and remember me functionality.
2. **Learning Goals**: Define goals with category tags, custom descriptions, target dates, and statuses (Pending, In Progress, Completed).
3. **Daily Study Logging**: Log study hours, specific topics covered, and self-reflection notes. Delete and edit logs dynamically.
4. **Study Streaks System**: Visualise streak counts with a glowing flame. Streaks increment automatically for consecutive study days and reset when days are missed.
5. **Personalized Recommendations**: A rule-based engine that matches your active goal categories and profile interests with curated tutorials, courses, and documentation.
6. **Achievement Badges**: Unlock badges for milestones (e.g., `First Goal`, `3 Day Streak`, `Goal Master` for 5 completed goals) accompanied by system notifications.
7. **Deadline & Missed Study Reminders**: Receive warnings on approaching target dates (<= 3 days left) and missed study logs on your dashboard.
8. **Admin Control Panel**: Restricted dashboard displaying global site metrics, system logs, user lists, and moderation controls (deleting users/goals).

---

## 📁 Project Structure

```text
learntrack/
├── app.py                  # Flask Application & Route Handlers
├── config.py               # Application Config (loads environment variables)
├── requirements.txt        # Backend dependencies
├── Procfile                # WSGI command for production hosting
├── runtime.txt             # Python runtime specification
├── .env.example            # Environment variables placeholder
├── static/
│   ├── css/
│   │   └── styles.css      # Custom styles (glassmorphism, animations, variables)
│   ├── js/
│   │   └── main.js         # Sidebar toggle, alert timers, deletion checks
│   ├── images/
│   │   └── default_avatar.png  # Fallback profile picture
│   └── uploads/            # Profile avatar uploads folder
├── templates/
│   ├── layout.html         # Base template wrapper
│   ├── auth/
│   │   ├── login.html      # Glassmorphic Login page
│   │   └── register.html   # Registration page
│   ├── dashboard/
│   │   └── index.html      # Student dashboard
│   ├── goals/
│   │   ├── index.html      # Goals list
│   │   ├── add.html        # Create goal form
│   │   └── edit.html       # Edit goal form
│   ├── profile/
│   │   └── index.html      # Profile & password change settings
│   ├── admin/
│   │   └── index.html      # Admin dashboard
│   └── includes/
│       ├── _messages.html  # Jinja flash alert helper
│       ├── sidebar.html    # Navigation sidebar
│       └── navbar.html     # Notifications & user profile dropdowns
├── database/
│   ├── schema.sql          # MySQL database tables DDL
│   └── sample_data.sql     # Seed data with default users & records
└── README.md               # User guide & developer instructions
```

---

## 💻 Tech Stack

- **Backend**: Python 3, Flask, Flask-MySQLdb, Flask-Bcrypt, Flask-WTF, Flask-Login, PyMySQL (transparent compilation fallback)
- **Frontend**: HTML5, CSS3, Bootstrap 5, Bootstrap Icons, JavaScript (ES6), Jinja2 templates
- **Database**: MySQL 8.x (Cascading foreign-key constraints, raw SQL queries only)
- **Deployment**: Render / Railway compatible WSGI Gunicorn stack

---

## ⚙️ Installation & Local Setup

Follow these steps to run the application locally on your computer:

### Prerequisites
- Python 3.8+ installed.
- MySQL Server installed and running locally.

### Step 1: Clone and Set Up Workspace
Navigate to the `learntrack` directory:
```bash
cd learntrack
```

### Step 2: Set Up Virtual Environment
Create and activate a virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```
> **Windows Note**: If installing `mysqlclient` fails (due to compiler constraints), the application will **automatically and transparently fallback** to using `PyMySQL` which is included in `requirements.txt`. No code changes are required!

### Step 4: Create MySQL Database
Log into your MySQL console and create the database:
```sql
CREATE DATABASE learntrack_db;
```

### Step 5: Configure Environment Variables
Copy the `.env.example` file to `.env`:
```bash
cp .env.example .env
```
Open `.env` and fill in your MySQL credentials:
```ini
SECRET_KEY=any_random_string_here
FLASK_ENV=development
PORT=5000

MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_mysql_root_password
MYSQL_DB=learntrack_db
```

### Step 6: Start the Application
```bash
python app.py
```
Upon the first startup, the application will **automatically run `database/schema.sql`** to initialize all database tables and seed them with the contents of `database/sample_data.sql`.

Open [http://localhost:5000](http://localhost:5000) in your browser to view the application!

---

## 🔑 Seeding / Demo Accounts

To test the application immediately, use the following pre-seeded credentials:

1. **Standard Student User**:
   - **Email**: `john@example.com` (or Username: `john_doe`)
   - **Password**: `password123`
   - *Simulates*: Pre-existing goals, logged hours, 2-day streak, 1 earned badge, and custom recommendations.

2. **Administrator User**:
   - **Email**: `admin@learntrack.com` (or Username: `admin`)
   - **Password**: `password123`
   - *Simulates*: View of all users, goals deletion, statistics tracking, and system feeds.

---

## 🚀 Production Deployment

### 1. Render Compatible
- Create a new **Web Service** on Render.
- Set **Runtime** to `Python`.
- Set **Build Command** to:
  ```bash
  pip install -r requirements.txt
  ```
- Set **Start Command** to:
  ```bash
  gunicorn app:app
  ```
- Under **Environment Variables**, add the environment variables defined in the `.env.example` file (pointing to your production MySQL instance, e.g. Render's database service or external RDS).

### 2. Railway Compatible
- Connect your GitHub repository to Railway.
- Railway will automatically detect the `Procfile` and `requirements.txt`.
- Add your MySQL environment variables in the variables tab.
- Railway will build and serve the application immediately.
