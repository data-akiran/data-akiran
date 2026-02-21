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

// Admin dashboard - HTML view of all subscribers
app.get('/admin', (req, res) => {
    const query = 'SELECT id, email, subscribed_at FROM subscribers ORDER BY subscribed_at DESC';
    
    db.all(query, [], (err, rows) => {
        if (err) {
            console.error('Database error:', err.message);
            return res.status(500).send('Database error occurred');
        }
        
        const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Email Subscribers Dashboard</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        
        .header {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        h1 {
            color: #667eea;
            margin-bottom: 10px;
            font-size: 2em;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
        }
        
        .stat-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .stat-label {
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }
        
        .actions {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s;
            font-size: 14px;
        }
        
        .btn-primary {
            background: white;
            color: #667eea;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 8px rgba(0,0,0,0.15);
        }
        
        .btn-secondary {
            background: rgba(255,255,255,0.2);
            color: white;
        }
        
        .btn-secondary:hover {
            background: rgba(255,255,255,0.3);
        }
        
        .search-box {
            padding: 12px;
            border: 2px solid #eee;
            border-radius: 8px;
            flex: 1;
            min-width: 200px;
            font-size: 14px;
        }
        
        .search-box:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .table-container {
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            font-weight: 600;
            position: sticky;
            top: 0;
        }
        
        tbody tr:hover {
            background-color: #f8f9fa;
        }
        
        .email-cell {
            font-family: 'Courier New', monospace;
            color: #333;
        }
        
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #666;
        }
        
        .empty-state-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        @media (max-width: 768px) {
            table {
                font-size: 0.85em;
            }
            
            th, td {
                padding: 10px 8px;
            }
            
            .actions {
                flex-direction: column;
            }
            
            .search-box {
                width: 100%;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📧 Email Subscribers Dashboard</h1>
            <p style="color: #666;">Manage and view all email subscriptions</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">${rows.length}</div>
                    <div class="stat-label">Total Subscribers</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${rows.filter(r => {
                        const date = new Date(r.subscribed_at);
                        const today = new Date();
                        return date.toDateString() === today.toDateString();
                    }).length}</div>
                    <div class="stat-label">Today</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${rows.filter(r => {
                        const date = new Date(r.subscribed_at);
                        const weekAgo = new Date();
                        weekAgo.setDate(weekAgo.getDate() - 7);
                        return date >= weekAgo;
                    }).length}</div>
                    <div class="stat-label">Last 7 Days</div>
                </div>
            </div>
        </div>
        
        <div class="actions">
            <button class="btn btn-primary" onclick="location.reload()">🔄 Refresh</button>
            <button class="btn btn-primary" onclick="exportCSV()">📥 Export CSV</button>
            <button class="btn btn-secondary" onclick="window.location.href='/'">← Back to Home</button>
            <input type="text" class="search-box" id="searchBox" placeholder="🔍 Search emails..." onkeyup="filterTable()">
        </div>
        
        <div class="table-container">
            ${rows.length === 0 ? `
                <div class="empty-state">
                    <div class="empty-state-icon">📭</div>
                    <h2>No subscribers yet</h2>
                    <p>Start collecting email subscriptions to see them here</p>
                </div>
            ` : `
                <table id="subscribersTable">
                    <thead>
                        <tr>
                            <th style="width: 80px;">ID</th>
                            <th>Email Address</th>
                            <th style="width: 200px;">Subscribed At</th>
                        </tr>
                    </thead>
                    <tbody>
                        ${rows.map(row => `
                            <tr>
                                <td>${row.id}</td>
                                <td class="email-cell">${row.email}</td>
                                <td>${new Date(row.subscribed_at).toLocaleString()}</td>
                            </tr>
                        `).join('')}
                    </tbody>
                </table>
            `}
        </div>
    </div>
    
    <script>
        function filterTable() {
            const input = document.getElementById('searchBox');
            const filter = input.value.toLowerCase();
            const table = document.getElementById('subscribersTable');
            
            if (!table) return;
            
            const rows = table.getElementsByTagName('tr');
            
            for (let i = 1; i < rows.length; i++) {
                const emailCell = rows[i].getElementsByClassName('email-cell')[0];
                if (emailCell) {
                    const emailText = emailCell.textContent || emailCell.innerText;
                    if (emailText.toLowerCase().indexOf(filter) > -1) {
                        rows[i].style.display = '';
                    } else {
                        rows[i].style.display = 'none';
                    }
                }
            }
        }
        
        function exportCSV() {
            const rows = ${JSON.stringify(rows)};
            
            let csv = 'ID,Email,Subscribed At\\n';
            rows.forEach(row => {
                csv += \`\${row.id},"\${row.email}","\${new Date(row.subscribed_at).toISOString()}"\\n\`;
            });
            
            const blob = new Blob([csv], { type: 'text/csv' });
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = \`subscribers_\${new Date().toISOString().split('T')[0]}.csv\`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);
        }
    </script>
</body>
</html>
        `;
        
        res.send(html);
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
    console.log(`Admin dashboard available at http://localhost:${PORT}/admin`);
    console.log('Press Ctrl+C to stop the server');
});