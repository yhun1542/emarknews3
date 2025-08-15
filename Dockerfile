FROM python:3.12

# Install Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs

WORKDIR /app

# Copy package files
COPY requirements.txt package.json ./

# Install Python dependencies
RUN pip install -r requirements.txt

# Install Node.js dependencies
RUN npm install

# Copy application files
COPY . .

EXPOSE 8000

CMD ["python", "main.py"]

