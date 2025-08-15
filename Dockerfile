FROM python:3.12

# Install Node.js (for future use)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy package files
COPY requirements.txt ./
COPY package.json ./

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Node.js dependencies (optional)
RUN npm install

# Copy application files
COPY main.py ./
COPY server.js ./
COPY frontend ./frontend

# Expose port
EXPOSE 8080

# Use uvicorn for production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

