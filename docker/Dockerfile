FROM python:3.12-slim

WORKDIR /app
COPY . /app
RUN pip install .
WORKDIR /app/quasi/gui/
EXPOSE 8080
ENV PORT 8080
CMD ["flet", "main.py", "--web", "--port", "8080"]
