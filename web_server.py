#!/usr/bin/env python3
import rasterio
import glob
import sys
from pyproj import Proj, transform
from bottle import *
BaseRequest.MEMFILE_MAX = 1e8
import time
import json
import os
import csv

s = time.time()
files = glob.glob("data/*.flt")
print("Loading rasters")
rasters = [rasterio.open(f) for f in files]
print(f"{round(time.time() - s, 4)} - loaded")

def contains(bounds, point):
    return point[0] > bounds.left and point[0] < bounds.right and point[1] > bounds.bottom and point[1] < bounds.top

app = Bottle()
@app.route('/', method=['GET', 'POST'])
def main():
    try:
        points = json.loads(request.params.get("points"))
    except:
        decoded = request.files.get("points").file.read().decode("utf-8").split('\n')
        reader = csv.reader(decoded, delimiter=",")
        points = []
        for row in reader:
            try:
                y = float(row[0])
                x = float(row[1])
                points.append((y, x))
            except:
                continue
    print(f"Got {len(points)} points")
    proj = request.params.get("proj", "EPSG:4326")
    inProj = Proj(init=proj)
    outProj = Proj(init='EPSG:2193')
    points = [transform(inProj, outProj, x, y) for y,x in points]

    results = [0] * len(points)
    for raster in rasters:
        for i, p in enumerate(points):
            if contains(raster.bounds, p):
                vals = raster.sample([p])
                results[i] = float(list(vals)[0][0])
    return {"results": results}

port = int(os.environ.get('PORT', 8080))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port, debug=True, server='gunicorn', workers=4)