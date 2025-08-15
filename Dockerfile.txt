FROM python:3.12
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
RUN npm install express axios @google-cloud/translate
COPY backend_AI_enhanced.js .
COPY frontend_final_merged.html .
COPY main.py .
COPY Procfile .
EXPOSE 8000
CMD ["python", "main.py"]