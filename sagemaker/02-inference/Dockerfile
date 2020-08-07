# https://aws.amazon.com/cn/releasenotes/available-deep-learning-containers-images/
FROM 727897471807.dkr.ecr.cn-northwest-1.amazonaws.com.cn/pytorch-inference:1.5.0-gpu-py36-cu101-ubuntu16.04


RUN apt-get install -y --no-install-recommends nginx \
    && rm -rf /var/lib/apt/lists/*


# RUN mkdir /opt/ml/code
WORKDIR /opt/ml/code
COPY source ./

WORKDIR /opt/ml/code/weights
RUN wget https://dikers-data.s3.cn-northwest-1.amazonaws.com.cn/dataset/craft_mlt_25k.pth

WORKDIR /opt/ml/code
RUN pip install --upgrade pip  -i https://mirrors.163.com/pypi/simple/
RUN pip install -r requirements.txt  -i https://mirrors.163.com/pypi/simple/

# Here we get all python packages.
# There's substantial overlap between scipy and numpy that we eliminate by
# linking them together. Likewise, pip leaves the install caches populated which uses
# a significant amount of space. These optimizations save a fair amount of space in the
# image, which reduces start up time.

RUN pip install flask gevent gunicorn boto3 && \
        rm -rf /root/.cache

# Set some environment variables. PYTHONUNBUFFERED keeps Python from buffering our standard
# output stream, which means that logs can be delivered to the user quickly. PYTHONDONTWRITEBYTECODE
# keeps Python from writing the .pyc files which are unnecessary in this case. We also update
# PATH so that the train and serve programs are found when the container is invoked.
WORKDIR /opt/ml/code

ENV PYTHONUNBUFFERED=TRUE
ENV PYTHONDONTWRITEBYTECODE=TRUE
ENV PATH="/opt/ml/code/:${PATH}"

ENTRYPOINT ["python3"]