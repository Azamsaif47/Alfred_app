# Use an official Node.js runtime as a parent image
FROM node:18-alpine

# Set the working directory in the container
WORKDIR /app

# Copy the package.json and package-lock.json
COPY frontend/package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend code into the container
COPY frontend/ .

# Build the React app
RUN npm run build

# Install 'serve' to run the production build
RUN npm install -g serve

# Expose the port for the React app
EXPOSE 3000

# Serve the app
CMD ["serve", "-s", "dist", "-l", "3000"]
