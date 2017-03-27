FROM python:2.7
RUN pip install PyMongo  && \
    pip install werkzeug  && \
    pip install json-rpc && \
    pip install cherrypy && \
    pip install hyperledger==0.1.5 && \
    pip install py2-ipaddress==3.4.1
RUN mkdir -p /opt/hyperTest/module
ADD ./JsonRPCServer.py /opt/hyperTest/
ADD ./__init__.py /opt/hyperTest/
ADD ./module /opt/hyperTest/module
RUN chmod 755 /opt/hyperTest/JsonRPCServer.py
WORKDIR /opt/hyperTest
EXPOSE 4000
