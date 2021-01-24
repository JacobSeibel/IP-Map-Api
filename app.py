import os
from flask import Flask, request
from flask_restful import Api
from flask_cors import CORS, cross_origin
import csv
import pandas as pd
import json
import sys
sys.path.append("..")
import ipv6_map_api.ipCount_pb2
import protobuf_to_dict
from cachetools import cached, TTLCache
import hashlib

app = Flask(__name__)
cache = TTLCache(maxsize=1024, ttl=600)
cors = CORS(app)
api = Api(app)

DATA_FILE = "data/GeoLite2-City-Blocks-IPv4.csv"
BIN_FILE = "data/ipCounts.bin"

def readDataFile():
    try:
       return open(DATA_FILE, 'rb').read()
    except IOError:
        print("Couldn't find the data file! Please provide this file: " + DATA_FILE)
        return {}

fileHash = hashlib.md5()
readBuf = readDataFile()
if readBuf:
    fileHash.update(readBuf)
cachedIpCounts = []

@cached(cache)
def readData():
    global fileHash
    global cachedIpCounts
    noData = False

    newHash = hashlib.md5()
    readBuf = readDataFile()
    if readBuf:
        newHash.update(readBuf)
    else:
        noData = True
    createNew = fileHash.digest() != newHash.digest()
    fileHash = newHash
    if not createNew and cachedIpCounts != []:
        return cachedIpCounts

    ipCountsProto = ipv6_map_api.ipCount_pb2.IPCounts()
    if not createNew:
        try:
            f = open(BIN_FILE, "rb")
            ipCountsProto.ParseFromString(f.read())
            f.close()
            createNew |= False
            print("Found a protocol buffer. Using that for the data!")
        except IOError:
            print("Could not open " + BIN_FILE + ". Creating a new one from data.")
            createNew = True
            if noData:
                print("...If I had any!! Please provide " + DATA_FILE)

    if createNew:
        print("Creating new protocol buffer")
        ipBlocks = []
        with open(DATA_FILE, newline='', encoding='utf-8') as csvfile:
            next(csvfile)
            blocksReader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in blocksReader:
                ipBlocks.append({
                    "latitude": row[7],
                    "longitude": row[8],
                })

        ipCountsDF = pd.DataFrame(ipBlocks).pivot_table(index=['latitude', 'longitude'], aggfunc='size')
        for ipCount in ipCountsDF.items():
            if ipCount[0][0] != '' and ipCount[0][1] != '':
                newCount = ipCountsProto.ipCounts.add()
                newCount.latitude = float(ipCount[0][0])
                newCount.longitude = float(ipCount[0][1])
                newCount.count = ipCount[1]
        f = open(BIN_FILE, "wb")
        f.write(ipCountsProto.SerializeToString())
        f.close()
    
    cachedIpCounts = protobuf_to_dict.protobuf_to_dict(ipCountsProto, including_default_value_fields=True)['ipCounts']
    return cachedIpCounts

def isInsideBounds(minLat, maxLat, minLng, maxLng, ipCount):
    lat = ipCount['latitude']
    lng = ipCount ['longitude']
    return lat > minLat and lat < maxLat and lng > minLng and lng < maxLng

@app.route("/ipCounts")
@cross_origin()
def getIPCounts():
    ipCounts = readData()
    result = ipCounts
    if "bounds" in request.args:
        bounds = json.loads(request.args["bounds"])
        if len(bounds) != 4:
            return {"errorMessage": "Must provide four corners of bounding box."}, 400
        minLat = bounds[0][0]
        maxLat = bounds[0][0]
        minLng = bounds[0][1]
        maxLng = bounds[0][1]
        for bound in bounds:
            if bound[0] < minLat: minLat = bound[0]
            if bound[0] > maxLat: maxLat = bound[0]
            if bound[1] < minLng: minLng = bound[1]
            if bound[1] > maxLng: maxLng = bound[1]
        result = [ipCount for ipCount in ipCounts if isInsideBounds(minLat, maxLat, minLng, maxLng, ipCount)]
    return {"result": result}, 200

app.run(debug=True)