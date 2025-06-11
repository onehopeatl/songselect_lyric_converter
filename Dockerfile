FROM python:3.13-alpine

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY /app /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 8080 for Flask
EXPOSE 8080

# Run with Flask dev server
#CMD ["python", "webapp.py"]

# Run with Gunicorn WSGI server
CMD ["gunicorn","--config", "gunicorn_config.py", "webapp:app"]
