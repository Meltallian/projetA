FROM nginx:1.26.3

# Install OpenSSL
RUN apt-get update && apt-get install -y openssl && rm -rf /var/lib/apt/lists/*

# Copy custom entrypoint script
COPY entrypoint/entrypoint.sh /docker-entrypoint.d/30-generate-certs.sh

# Make the script executable
RUN chmod +x /docker-entrypoint.d/30-generate-certs.sh