# 📧 Email Subscription App

A simple full-stack email subscription application that allows users to subscribe via a web form and stores subscriber emails in a SQLite database.

---

## 🚀 Features

- Clean HTML frontend with subscription form
- REST API backend using Node.js and Express
- SQLite database for persistent storage
- Admin dashboard to view and manage subscribers
- CSV export of subscriber list
- Email search and filtering
- Subscriber count stats (total, today, last 7 days)
- Lightweight and easy to run locally

---

## 🏗 Project Architecture

```
email-subscription-app/
├── server.js
├── package.json
├── index.html
└── data/
    └── emails.db
```

---

## 🛠️ Technology Stack

- **Frontend**: HTML, CSS, JavaScript
- **Backend**: Node.js, Express
- **Database**: SQLite (via `sqlite3`)
- **Containerization**: Docker

---

## 🏃 Quick Start

### Prerequisites

- Node.js 18+ installed
- npm installed

### Installation

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd email-subscription-app
```

2. **Install dependencies**:
```bash
npm install
```

3. **Start the server**:
```bash
node server.js
```

4. **Access the app**:
   - **Subscription Form**: http://localhost:3000
   - **Admin Dashboard**: http://localhost:3000/admin

### Run with Docker

```bash
docker compose up -d --build
```

---

## 📖 API Documentation

### `POST /api/subscribe`
Subscribe a new email address.

**Request body:**
```json
{
  "email": "user@example.com"
}
```

**Response (success — 201):**
```json
{
  "message": "Successfully subscribed!",
  "id": 1
}
```

**Response (duplicate — 409):**
```json
{
  "error": "This email is already subscribed"
}
```

**Response (invalid — 400):**
```json
{
  "error": "Invalid email format"
}
```

---

### `GET /api/subscribers`
Get all subscribers.

**Response:**
```json
{
  "count": 2,
  "subscribers": [
    { "id": 1, "email": "user@example.com", "subscribed_at": "2024-01-01T00:00:00Z" }
  ]
}
```

---

### `GET /api/count`
Get total subscriber count.

**Response:**
```json
{ "count": 42 }
```

---

### `GET /admin`
Admin dashboard — HTML view with subscriber table, stats, search, and CSV export.

---

## 🗄️ Database

The app uses SQLite stored at `./data/emails.db` with a single `subscribers` table:

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key (autoincrement) |
| email | TEXT | Subscriber email (unique) |
| subscribed_at | DATETIME | Subscription timestamp |

The `data/` directory is created automatically on first run if it doesn't exist.

---

## 🐛 Troubleshooting

### Port already in use
```bash
# Find and kill the process using port 3000
lsof -i :3000
kill -9 <PID>
```

### Database issues
```bash
# Delete and recreate the database
rm -rf ./data/emails.db
node server.js
```

### Docker volume data lost
The database is stored in `./data/emails.db`. Make sure your Docker volume is mounted correctly so data persists between restarts.

---

## 🔄 Development

### Watch logs (Docker)
```bash
docker compose logs -f
```

### Restart the app
```bash
docker compose restart
```

---

## 🛑 Stopping the App

```bash
# If running locally
Ctrl+C

# If running with Docker
docker compose down
```

The server handles graceful shutdown automatically — the SQLite connection is closed cleanly on `Ctrl+C`.

---

## 📝 License

MIT License - feel free to use for your projects!

---

Built with ❤️ using Node.js and Express