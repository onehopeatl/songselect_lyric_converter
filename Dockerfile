FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy project files into the container
COPY /app /app

# Install dependencies
RUN pip install -r requirements.txt

# Expose port 8080 for Flask
EXPOSE 8080

CMD ["python", "webapp.py"]
