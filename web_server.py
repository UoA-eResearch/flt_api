#!/usr/bin/env python3
import rasterio
import glob
import sys
from pyproj import Proj, transform
from bottle import Bottle, run, request
import time
import json

s = time.time()
files = glob.glob("data/*.flt")
print("Loading rasters")
rasters = [rasterio.open(f) for f in files]
print(f"{round(time.time() - s, 4)} - loaded")

def contains(bounds, point):
    return point[0] > bounds.left and point[0] < bounds.right and point[1] > bounds.bottom and point[1] < bounds.top

app = Bottle()
@app.route('/')
def main():
    points = json.loads(request.params.get("points"))
    print(points)
    proj = request.params.get("proj", "EPSG:4326")
    inProj = Proj(init=proj)
    outProj = Proj(init='EPSG:2193')
    points = [transform(inProj, outProj, x, y) for y,x in points]
    print(points)

    results = [0] * len(points)
    for raster in rasters:
        for i, p in enumerate(points):
            if contains(raster.bounds, p):
                vals = raster.sample([p])
                results[i] = float(list(vals)[0][0])
    return {"results": results}

run(app, host='localhost', port=8080)
