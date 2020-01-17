FROM python:3-alpine

COPY requirements.txt /

RUN apk --update add --virtual build-dependencies build-base tzdata \
  && cp /usr/share/zoneinfo/Etc/UTC /etc/localtime \
  && pip install -r /requirements.txt \
  && apk del build-dependencies tzdata \
  && rm -fR /root/.cache

WORKDIR /tmp/x
COPY nibe_mqtt/*py ./nibe_mqtt/
COPY setup.py README.md MANIFEST.in LICENSE requirements.txt ./
RUN  pip install .

WORKDIR /nibe-mqtt
COPY conf/*yml ./conf/

ENTRYPOINT [ "nibe-mqtt" ]
