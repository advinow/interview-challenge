FROM python:3.10

ENV PYTHONPATH "${PYTHONPATH}:/"
ENV PORT=8013

RUN pip install --upgrade pip

COPY requirements/requirements.txt .

RUN pip install -r requirements.txt

COPY app/ app/