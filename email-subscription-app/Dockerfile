# Use official Node.js runtime as base image
FROM node:20-alpine

# Set working directory in container
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install --production

# Copy application files
COPY . .

# Expose port 3000
EXPOSE 3000

# Create volume for database persistence
VOLUME ["/app/data"]

# Start the application
CMD ["node", "server.js"]
