FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN npm install express axios @google-cloud/translate
COPY server.js .
COPY index.html .
COPY main.py .
COPY Procfile .
EXPOSE 8000
CMD ["python", "main.py"]