FROM python:3.11-slim

# Create and use a directory for the app
WORKDIR /app

# Copy requirements and install
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . /app/

# Expose the port used by Gunicorn
EXPOSE 5000

# Run the Flask app via Gunicorn
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
