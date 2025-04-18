-- Add new tables for Tasks and Requests

-- Tasks table with unique ID and description
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Task owners (many-to-many relationship)
CREATE TABLE IF NOT EXISTS task_owners (
    task_id INTEGER,
    user_id INTEGER,
    PRIMARY KEY (task_id, user_id),
    FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Requests table with unique ID, solicitor and description
CREATE TABLE IF NOT EXISTS requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitor_id INTEGER NOT NULL,
    description TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (solicitor_id) REFERENCES users(id)
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_task_owners_task_id ON task_owners(task_id);
CREATE INDEX IF NOT EXISTS idx_task_owners_user_id ON task_owners(user_id);
CREATE INDEX IF NOT EXISTS idx_requests_solicitor ON requests(solicitor_id);