-- LearnTrack Seed Data
-- Default passwords are 'password123' (hashed using Bcrypt: $2b$12$R9h/lIPzNgbpcZG.Zg8A9uJgYc9o4f0gGkL1r3y/5e.QkP4F5iMye)

USE learntrack_db;

-- Clear tables (avoid duplication when re-running seed script)
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE badges;
TRUNCATE TABLE notifications;
TRUNCATE TABLE recommendations;
TRUNCATE TABLE streaks;
TRUNCATE TABLE progress_logs;
TRUNCATE TABLE goals;
TRUNCATE TABLE users;
SET FOREIGN_KEY_CHECKS = 1;

-- 1. Insert Users
INSERT INTO users (id, username, email, password, learning_style, interests, profile_image, is_admin, created_at)
VALUES 
(1, 'admin', 'admin@learntrack.com', '$2b$12$R9h/lIPzNgbpcZG.Zg8A9uJgYc9o4f0gGkL1r3y/5e.QkP4F5iMye', 'Reading/Writing', 'Web Development, Databases, Security', 'default_avatar.png', TRUE, '2026-06-01 10:00:00'),
(2, 'john_doe', 'john@example.com', '$2b$12$R9h/lIPzNgbpcZG.Zg8A9uJgYc9o4f0gGkL1r3y/5e.QkP4F5iMye', 'Visual', 'Python, Machine Learning, Web Design', 'default_avatar.png', FALSE, '2026-06-05 09:00:00');

-- 2. Insert Goals for john_doe (User 2)
INSERT INTO goals (id, user_id, title, description, category, target_date, status, created_at)
VALUES
(1, 2, 'Master Python Basics', 'Complete OOP concepts, decorators, generators, and standard libraries.', 'Python', '2026-07-15', 'In Progress', '2026-06-05 09:15:00'),
(2, 2, 'Build LearnTrack Portfolio', 'Build a production-ready Flask tracking app with a raw MySQL backend.', 'Web Development', '2026-06-25', 'In Progress', '2026-06-06 14:00:00'),
(3, 2, 'Understand SQL Joins', 'Learn INNER, LEFT, RIGHT, and FULL OUTER joins with complex aggregate groupings.', 'Databases', '2026-06-10', 'Completed', '2026-06-05 09:30:00');

-- 3. Insert Progress Logs for john_doe (User 2)
INSERT INTO progress_logs (id, user_id, goal_id, study_date, hours, topic, notes, created_at)
VALUES
(1, 2, 3, '2026-06-08', 2.50, 'SQL Inner and Outer Joins', 'Practiced joins with aggregate operations. Understood ON vs WHERE clauses.', '2026-06-08 20:00:00'),
(2, 2, 3, '2026-06-10', 3.00, 'SQL Subqueries & Completed Goal', 'Wrote subqueries and self joins. Finished all planned SQL join exercises.', '2026-06-10 18:30:00'),
(3, 2, 1, '2026-06-11', 1.50, 'Python Decorators', 'Understood decorators with and without arguments. Wrote timing decorator.', '2026-06-11 21:00:00'),
(4, 2, 2, '2026-06-12', 4.00, 'Flask Session Setup', 'Configured Flask-Login and session handlers. Tested route protection.', '2026-06-12 11:30:00');

-- 4. Insert Streaks for Users
INSERT INTO streaks (user_id, current_streak, longest_streak, last_checkin)
VALUES
(1, 0, 0, NULL),
(2, 2, 2, '2026-06-12'); -- Last checked in today, current streak is 2 days (June 11 and June 12)

-- 5. Insert Sample Recommendations for john_doe
INSERT INTO recommendations (user_id, title, resource_link, category, resource_type)
VALUES
(2, 'Official Python Tutorial', 'https://docs.python.org/3/tutorial/index.html', 'Python', 'Documentation'),
(2, 'Flask Web Development Course - freeCodeCamp', 'https://www.youtube.com/watch?v=qbLc5a9jdXo', 'Web Development', 'Course'),
(2, 'W3Schools SQL Join Reference', 'https://www.w3schools.com/sql/sql_join.asp', 'Databases', 'Article');

-- 6. Insert Sample Notifications for john_doe
INSERT INTO notifications (user_id, message, is_read, created_at)
VALUES
(2, 'Welcome to LearnTrack! Set your first goal to begin your journey.', TRUE, '2026-06-05 09:00:00'),
(2, 'Congratulations! You earned the badge: First Goal!', FALSE, '2026-06-05 09:15:00'),
(2, 'Goal "Understand SQL Joins" has been completed successfully!', FALSE, '2026-06-10 18:30:00');

-- 7. Insert Badges for john_doe
INSERT INTO badges (user_id, badge_name, earned_at)
VALUES
(2, 'First Goal', '2026-06-05 09:15:00');
