FROM python:3
ADD ssl/cert.pem /
ADD ssl/key.pem /
RUN pip install sanic aiofiles
ADD src/main.py /
CMD [ "python", "./main.py" ]
