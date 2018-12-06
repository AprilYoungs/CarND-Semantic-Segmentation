#!/usr/bin/env bash

echo "Downloading data"
curl https://s3.eu-central-1.amazonaws.com/avg-kitti/data_road.zip > data_road.zip

echo "Unzip files"
unzip data_road.zip -d data/

rm data_road.zip

echo "All done!"