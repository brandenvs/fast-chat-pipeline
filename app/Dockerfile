FROM python:3.11-slim

WORKDIR /srv

# deps
COPY requirements.txt /srv/requirements.txt
RUN pip install --no-cache-dir -r /srv/requirements.txt

# copy root
COPY . /srv

ENV PYTHONPATH=/srv

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
