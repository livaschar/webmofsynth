# Use the official Nginx image from the Docker Hub
FROM nginx:alpine

# Remove the default configuration
RUN rm /etc/nginx/conf.d/default.conf

# Copy the custom Nginx configuration file into the container
COPY nginx.conf /etc/nginx/nginx.conf

# Copy static files and templates into the Nginx HTML directory
COPY static/ /usr/share/nginx/html/static/
COPY templates/ /usr/share/nginx/html/templates/

# Expose port 80
EXPOSE 80
