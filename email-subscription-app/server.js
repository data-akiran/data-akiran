const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
const bodyParser = require('body-parser');

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(bodyParser.json());
app.use(express.static(path.join(__dirname)));

// Initialize SQLite database
const db = new sqlite3.Database('./emails.db', (err) => {
    if (err) {
        console.error('Error opening database:', err.message);
    } else {
        console.log('Connected to the SQLite database.');
        
        // Create table if it doesn't exist
        db.run(`
            CREATE TABLE IF NOT EXISTS subscribers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                subscribed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        `, (err) => {
            if (err) {
                console.error('Error creating table:', err.message);
            } else {
                console.log('Subscribers table is ready.');
            }
        });
    }
});

// API endpoint to handle email subscription
app.post('/api/subscribe', (req, res) => {
    const { email } = req.body;
    
    // Validate email
    if (!email) {
        return res.status(400).json({ error: 'Email is required' });
    }
    
    // Basic email validation
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
        return res.status(400).json({ error: 'Invalid email format' });
    }
    
    // Insert email into database
    const query = 'INSERT INTO subscribers (email) VALUES (?)';
    
    db.run(query, [email.toLowerCase()], function(err) {
        if (err) {
            if (err.message.includes('UNIQUE constraint failed')) {
                return res.status(409).json({ error: 'This email is already subscribed' });
            }
            console.error('Database error:', err.message);
            return res.status(500).json({ error: 'Database error occurred' });
        }
        
        console.log(`New subscriber added: ${email} (ID: ${this.lastID})`);
        res.status(201).json({ 
            message: 'Successfully subscribed!',
            id: this.lastID 
        });
    });
});

// API endpoint to get all subscribers (for admin purposes)
app.get('/api/subscribers', (req, res) => {
    const query = 'SELECT id, email, subscribed_at FROM subscribers ORDER BY subscribed_at DESC';
    
    db.all(query, [], (err, rows) => {
        if (err) {
            console.error('Database error:', err.message);
            return res.status(500).json({ error: 'Database error occurred' });
        }
        
        res.json({ 
            count: rows.length,
            subscribers: rows 
        });
    });
});

// API endpoint to check subscriber count
app.get('/api/count', (req, res) => {
    const query = 'SELECT COUNT(*) as count FROM subscribers';
    
    db.get(query, [], (err, row) => {
        if (err) {
            console.error('Database error:', err.message);
            return res.status(500).json({ error: 'Database error occurred' });
        }
        
        res.json({ count: row.count });
    });
});

// Serve the main HTML file
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'index.html'));
});

// Handle graceful shutdown
process.on('SIGINT', () => {
    db.close((err) => {
        if (err) {
            console.error('Error closing database:', err.message);
        } else {
            console.log('Database connection closed.');
        }
        process.exit(0);
    });
});

// Start server
app.listen(PORT, () => {
    console.log(`Server is running on http://localhost:${PORT}`);
    console.log('Press Ctrl+C to stop the server');
});