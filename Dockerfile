FROM python:3
ADD cert.pem /
ADD key.pem /
RUN pip install sanic json-logging
ADD main.py /
CMD [ "python", "./main.py" ]
