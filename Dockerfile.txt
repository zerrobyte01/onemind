FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir scikit-learn numpy

CMD ["bash", "start.sh"]