#!/bin/bash

# 下载Globe.GL和Three.js库到本地
# 这样就不需要依赖CDN了

cd /home/ccc/pq-ntor-experiment/sagin-experiments/demo

echo "下载Three.js..."
wget -q https://cdn.jsdelivr.net/npm/three@0.154.0/build/three.min.js -O three.min.js

echo "下载Globe.GL..."
wget -q https://cdn.jsdelivr.net/npm/globe.gl@2.31.0/dist/globe.gl.min.js -O globe.gl.min.js

echo "下载地球纹理..."
mkdir -p textures
wget -q https://unpkg.com/three-globe/example/img/earth-blue-marble.jpg -O textures/earth-blue-marble.jpg
wget -q https://unpkg.com/three-globe/example/img/earth-topology.png -O textures/earth-topology.png
wget -q https://unpkg.com/three-globe/example/img/night-sky.png -O textures/night-sky.png

echo "下载国界线数据..."
wget -q https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json -O countries-110m.json

echo "✅ 下载完成！"
ls -lh *.js textures/ countries-110m.json
