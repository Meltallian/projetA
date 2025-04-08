FROM python:3.9

WORKDIR /code

# Install dependencies
COPY requirements.txt /code/
RUN pip install -r requirements.txt

# Copy project
COPY . /code/

# Prepare static files directory but don't run collectstatic during build
# (we'll do this after the container starts)
RUN mkdir -p /code/staticfiles /code/media
