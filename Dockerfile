FROM python:3-alpine

COPY requirements.txt /
RUN pip install -r /requirements.txt

WORKDIR /nibe-mqtt
COPY conf/*yml /nibe-mqtt/conf/
COPY *.py /nibe-mqtt/

ENTRYPOINT [ "python", "./nibe-mqtt.py" ]

