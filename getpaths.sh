#! /bin/sh

# Download elevation data for Laguna Seca from Google Maps

p=512
p0=`expr $p - 1`
for x in `seq 0 $p0`; do
    echo "16 k _121.7585 $x $p / 0.01 * + p" >dcf
    xr=`dc -f dcf 2>/dev/null`
#    echo $xr
#    for y in `seq 0 $p0`; do
#       echo '8 k' >dcf
#	echo "36.579 $y $p / 0.001 * + p" >>dcf
#    done
    wget "https://maps.googleapis.com/maps/api/elevation/xml?path=36.579,$xr|36.589,$xr&samples=$p" -O path${x}.xml
#    echo "path${x}.xml"
    sleep 0.5
done
