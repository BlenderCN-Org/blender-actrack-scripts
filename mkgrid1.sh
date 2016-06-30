#! /bin/sh
for x in `seq 0 511`; do
    grep '\(lat.*lat\|lng.*lng\|elev.*elev\)' < path$x.xml |sed s,'</elevation>,#,' |sed s,'<[^>]*>,,g' |tr '\n' ' '|sed -e 's,#,\
,g' -e 's,   *, ,g'
done |sed  -e 's,^ ,,g'
