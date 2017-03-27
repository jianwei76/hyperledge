#!/bin/bash
DB=$1
BlockChain=$2
rpc=$3
sudo docker rm -f $rpc
sudo docker run --name $rpc -p 4000:4000 cttirpc:v1 python ./JsonRPCServer.py $DB $BlockChain
