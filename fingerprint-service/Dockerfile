FROM node:18 

# Set the working directory
WORKDIR /app

# Install nmap
RUN apt-get update && apt-get install nmap -y

# Copy package.json and package-lock.json
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy the rest of the application code
COPY . .

# Start Node Program
CMD ["npm", "start"]
