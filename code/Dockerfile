FROM ubuntu:20.04
COPY . /code
WORKDIR /code

RUN apt update
RUN apt-get install -y libglib2.0-0 libsm6 libxrender1 libxext6
RUN apt-get update \
     && apt-get install -y \
        libgl1-mesa-glx \
        libx11-xcb1 \
     && apt-get clean all \
     && rm -r /var/lib/apt/lists/*
RUN apt-get update && apt-get install -y \
    software-properties-common
RUN add-apt-repository universe
RUN apt-get update && apt-get install -y \
    python3-pip
RUN apt-get clean all
RUN pip3 install --upgrade pip
RUN rm -r /var/lib/apt/lists/*
RUN pip3 install --no-cache-dir -r  requirements.txt
RUN pip3 install --no-cache-dir python-magic
EXPOSE 5000
CMD flask run --host=0.0.0.0