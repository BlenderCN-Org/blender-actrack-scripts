#! /bin/sh

# Convert path*.xml files into a .grid file for import into Blender

echo "512 512 0.0001 0.0001 -121.7585 36.579"
./mkgrid1.sh |sed  -e 's,^ ,,g'
