# frontend/Dockerfile

# --- Stage 1: Build the React application ---
FROM node:20-alpine as builder
WORKDIR /app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
RUN npm run build

# --- Stage 2: Serve the application using Nginx ---
FROM nginx:1.25-alpine
# WORKDIR /usr/share/nginx/html # WORKDIR not strictly needed if using absolute paths

# Copy the build output from the builder stage explicitly to Nginx's web root
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy our custom Nginx configuration from the build context (./frontend)
COPY nginx.default.conf /etc/nginx/conf.d/default.conf

# Remove the debugging lines we added earlier
# RUN echo "--- Debug: ..."

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]