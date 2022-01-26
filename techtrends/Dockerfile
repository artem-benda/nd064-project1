FROM python:2.7
LABEL maintainer="Artem Benda"

COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt

# Init sqlite database
RUN python init_db.py

# Expose port 3111 for web app
EXPOSE 3111

# command to run on container start
CMD [ "python", "app.py" ]
