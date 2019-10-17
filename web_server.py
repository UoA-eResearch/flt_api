#!/usr/bin/env python3
import rasterio
import glob
import sys
from pyproj import Transformer
from bottle import *
BaseRequest.MEMFILE_MAX = int(1e8)
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
    points = None
    if request.params.get("points"):
        try:
            points = json.loads(request.params.get("points"))
        except BaseException as e:
            response.status = 400
            return {"error": f"JSON decode error"}
    elif request.files.get("points"):
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
    if not points:
        response.status = 400
        return {"error": "No points given"}
    if type(points) != list or type(points[0]) not in [list, tuple]:
        response.status = 400
        return {"error": "Please give a list of coordinates"}
    print(f"Got {len(points)} points")
    proj = request.params.get("proj", "EPSG:4326")
    try:
        transformer = Transformer.from_crs(proj, "EPSG:2193", always_xy=True)
        points = [transformer.transform(x, y) for y,x in points]
        print("Points reprojected")
    except BaseException as e:
        response.status = 400
        e = str(e)[1:].strip("'")
        return {"error": f"Projection conversion error: {e}"}

    results = [0] * len(points)
    for raster in rasters:
        for i, p in enumerate(points):
            if contains(raster.bounds, p):
                vals = raster.sample([p])
                results[i] = float(list(vals)[0][0])
    payload = {"results": results}
    if len(points[0]) > 2:
        payload["warnings"] = ["More than 2 columns given - only the first 2 were used. Please only send 2."]
    return payload

port = int(os.environ.get('PORT', 8080))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=port, debug=True, server='gunicorn', workers=4, timeout=600)