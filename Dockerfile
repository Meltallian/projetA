FROM python:3.9

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install postgres client for health check
RUN apt-get update && apt-get install -y postgresql-client

# Add a healthcheck script
COPY wait-for-postgres.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/wait-for-postgres.sh

COPY . .

# Use the healthcheck script as an entrypoint
ENTRYPOINT ["/usr/local/bin/wait-for-postgres.sh"]