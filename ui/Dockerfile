# Stage 1: Build the React App
FROM node:18 AS builder

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the React app for production
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:stable-alpine

# Set the working directory for Nginx
WORKDIR /usr/share/nginx/html

# Remove the default Nginx index page
RUN rm -rf ./*

# Copy the built app from the builder stage
COPY --from=builder /app/dist .

# Copy a custom Nginx configuration file (optional)
COPY ./nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80 for the application
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
