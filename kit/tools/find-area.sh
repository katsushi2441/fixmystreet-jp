#!/usr/bin/env bash
# 経度 緯度 から MapIt Global（OpenStreetMap の行政境界）の区域 id を引く
#   tools/find-area.sh 136.9066 35.1815
curl -s "https://global.mapit.mysociety.org/point/4326/$1,$2" | python3 -c "import sys,json; d=json.load(sys.stdin); [print(v['name'], k, v['type']) for k,v in d.items()]"
