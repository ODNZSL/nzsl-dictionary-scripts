FROM python:3
RUN apt-get update &&\
    apt-get install -qqy imagemagick optipng &&\
    mkdir /usr/src/app &&\
    rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/app
ADD . /usr/src/app
RUN pip install -r requirements.txt

ENTRYPOINT ["python"]
