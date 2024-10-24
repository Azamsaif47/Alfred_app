git # Build stage
FROM node:18-alpine AS build

# Set the working directory
WORKDIR /app

# Copy the package.json and lock file to install dependencies
COPY frontend/package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the rest of the frontend code
COPY frontend/ .

# Build the app using environment variables
ARG VITE_API_URL
ENV VITE_API_URL=$VITE_API_URL
RUN npm run build

# Production stage with Nginx
FROM nginx:alpine

# Copy the built React files from the build stage
COPY --from=build /app/dist /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Run Nginx
CMD ["nginx", "-g", "daemon off;"]
