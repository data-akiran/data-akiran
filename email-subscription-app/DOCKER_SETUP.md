docker build -t email-subscription-app .

# 2. Run the container
docker run -d -p 3000:3000 --name email-app email-subscription-app

# 3. Open browser
# Go to: http://localhost:3000
```

---

## Docker Commands Reference

### Start the Application

```bash
# Using docker-compose (recommended)
docker-compose up -d

# Using docker
docker start email-app
```

### Stop the Application

```bash
# Using docker-compose
docker-compose down

# Using docker
docker stop email-app
```

### View Logs

```bash
# Using docker-compose
docker-compose logs -f

# Using docker
docker logs -f email-app
```

### Restart the Application

```bash
# Using docker-compose
docker-compose restart

# Using docker
docker restart email-app
```

### Remove Everything (Clean Slate)

```bash
# Using docker-compose
docker-compose down -v

# Using docker
docker stop email-app
docker rm email-app
docker rmi email-subscription-app
```

---

## File Structure

Make sure all these files are in your project folder:

```
email-subscription-app/
├── Dockerfile              # Docker configuration
├── docker-compose.yml      # Docker Compose configuration
├── .dockerignore          # Files to exclude from Docker
├── package.json           # Node.js dependencies
├── server.js              # Backend server
├── index.html             # Frontend website
└── emails.db              # Database (created automatically)
```

---

## How It Works

1. **Dockerfile** - Defines how to build the container
   - Uses Node.js 20 Alpine (lightweight)
   - Installs dependencies
   - Copies your code
   - Exposes port 3000

2. **docker-compose.yml** - Makes it easy to run
   - Builds and runs the container
   - Maps port 3000 to your Mac
   - Persists database data
   - Auto-restarts if it crashes

3. **Container** - Isolated environment
   - Has Node.js built-in
   - Runs your application
   - Database persists even when stopped

---

## Database Persistence

Your email data is saved in `emails.db` file which persists even when you stop the container.

**View database content:**

```bash
# Access the running container
docker exec -it email-app sh

# Inside container, view database
sqlite3 emails.db
SELECT * FROM subscribers;
.exit
exit
```

**Backup database:**

```bash
# Copy database from container to your Mac
docker cp email-app:/app/emails.db ./emails-backup.db
```

---

## Accessing the Application

Once running, you can access:

- **Website**: http://localhost:3000
- **API - All subscribers**: http://localhost:3000/api/subscribers
- **API - Count**: http://localhost:3000/api/count

---

## Troubleshooting

### "Cannot connect to the Docker daemon"

**Solution:** Docker Desktop is not running
1. Open Docker Desktop application
2. Wait for it to start (whale icon appears in menu bar)
3. Try your docker commands again

### "port is already allocated"

**Solution:** Port 3000 is already in use

```bash
# Option 1: Stop the conflicting container
docker ps
docker stop <container-id>

# Option 2: Use a different port
# Edit docker-compose.yml, change "3000:3000" to "8080:3000"
# Then access at http://localhost:8080
```

### "No such file or directory"

**Solution:** You're not in the project folder

```bash
# Find your project
ls ~/Desktop
ls ~/Documents

# Navigate to it
cd ~/Desktop/email-subscription-app
```

### Container keeps restarting

**Solution:** Check the logs to see what's wrong

```bash
docker-compose logs -f
# or
docker logs email-app
```

### Want to rebuild after code changes

```bash
# Stop and remove container
docker-compose down

# Rebuild and start
docker-compose up -d --build
```

---

## Testing the Application

### 1. Test the Website

1. Go to http://localhost:3000
2. Enter email: test@example.com
3. Click "Subscribe Now"
4. Should see: "Successfully subscribed!"

### 2. Test the API

```bash
# Subscribe via API
curl -X POST http://localhost:3000/api/subscribe \
  -H "Content-Type: application/json" \
  -d '{"email":"api-test@example.com"}'

# Get all subscribers
curl http://localhost:3000/api/subscribers

# Get count
curl http://localhost:3000/api/count
```

### 3. Check Container Status

```bash
# See running containers
docker ps

# Should show:
# CONTAINER ID   IMAGE                    STATUS         PORTS
# abc123...      email-subscription-app   Up 2 minutes   0.0.0.0:3000->3000/tcp
```

---

## Production Deployment

For deploying to production:

1. **Use environment variables:**
   ```yaml
   # In docker-compose.yml
   environment:
     - NODE_ENV=production
     - PORT=3000
     - DB_PATH=/app/data/emails.db
   ```

2. **Use volumes for persistence:**
   ```yaml
   volumes:
     - ./data:/app/data
   ```

3. **Add a reverse proxy** (nginx, Caddy)

4. **Use Docker secrets** for sensitive data

5. **Enable HTTPS**

---

## Advantages of Using Docker

✅ No need to install Node.js on your Mac
✅ Consistent environment (works everywhere)
✅ Easy to deploy to servers
✅ Isolated from your system
✅ Easy to start/stop/restart
✅ Can run multiple versions simultaneously
✅ Easy cleanup (just delete container)

---

## Common Workflows

### Daily Development

```bash
# Start work
docker-compose up -d

# View logs while developing
docker-compose logs -f

# Stop work
docker-compose down
```

### Making Code Changes

```bash
# Stop container
docker-compose down

# Edit your code (server.js, index.html, etc.)

# Rebuild and restart
docker-compose up -d --build
```

### Sharing with Team

```bash
# Just share these files:
# - Dockerfile
# - docker-compose.yml
# - All application files

# They run:
docker-compose up -d

# Everything works identically!
```

---

## Next Steps

1. ✅ Install Docker Desktop
2. ✅ Put all project files in one folder
3. ✅ Run `docker-compose up -d`
4. ✅ Open http://localhost:3000
5. ✅ Test the email form

You're all set! 🎉

---

## Need Help?

Check logs first:
```bash
docker-compose logs -f
```

Common issues:
- Docker not running → Open Docker Desktop
- Port in use → Change port in docker-compose.yml
- Build fails → Check Dockerfile syntax
- Can't connect → Check firewall settings

For more help, share the error message and what command you ran.
