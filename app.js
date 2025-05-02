const express = require('express');
const mysql = require('mysql2/promise');
const app = express();
const PORT = 8080;

// Parse JSON request bodies
app.use(express.json());

// Database configuration
const dbConfig = {
  host: process.env.DB_HOST || 'mysql',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || 'root',
  database: process.env.DB_NAME || 'simpledb'
};

// Create MySQL connection pool
const pool = mysql.createPool(dbConfig);

// Initialize database with a users table if it doesn't exist
async function initDatabase() {
  try {
    const connection = await pool.getConnection();
    
    console.log('Connected to MySQL database');
    
    // Create users table if it doesn't exist
    await connection.query(`
      CREATE TABLE IF NOT EXISTS users (
        id INT AUTO_INCREMENT PRIMARY KEY,
        name VARCHAR(100)UNIQUE NOT NULL,
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        role ENUM('user', 'admin') DEFAULT 'admin',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
      )
    `);
    
    console.log('Database initialized successfully');
    connection.release();
  } catch (err) {
    console.error('Error initializing database Retrying after 5 seconds:', err);
    // Keep trying to connect
    setTimeout(initDatabase, 5000);
  }
}

// Initialize database on startup
initDatabase();

// Root endpoint
app.get('/', (req, res) => {
  res.json({ message: 'This is the database server!' });
});

// Get all users endpoint
app.get('/users', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM users');
    console.error("This is working as expected");
    res.json(rows);
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
});

// Add user endpoint
app.post('/create', async (req, res) => {
  try {
    const { name, email, password } = req.body;
    if (!name || !email || !password) {
      return res.status(400).json({ error: 'Name, email, and password are required' });
    }
    
    const [result] = await pool.query(
      'INSERT INTO users (name, email, password) VALUES (?, ?, ?)',
      [name, email, password]
    );
    
    res.status(201).json({ 
      id: result.insertId,
      name,
      email
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
});

// Login endpoint
app.post('/login', async (req, res) => {
  try {
    const { name, password } = req.body;
    if (!name || !password) {
      return res.status(400).json({ error: 'name and password are required' });
    }
    
    // SQL query to check if the user and password exist and match
    const [rows] = await pool.query(
      'SELECT id, name, email FROM users WHERE name = ? AND password = ?',
      [name, password]
    );
    
    if (rows.length === 0) {
      return res.status(401).json({ error: 'Invalid credentials' });
    }
    
    // User authenticated successfully
    res.status(200).json({ 
      message: 'Login successful',
      user: rows[0]
    });
  } catch (err) {
    console.error(err);
    res.status(500).json({ error: 'Database error' });
  }
});

app.listen(PORT, () => {
  console.log(`Hello World API server running on port ${PORT}`);
});