#!/usr/bin/env python
"""
Scraper that gets the tree data from mapa.um.warszawa.pl for given boundaries.
Note that:
- EPSG:2178 projection is used (http://spatialreference.org/ref/epsg/2178/)
- Coordinates range for Warsaw are simplified to fit in a box
- the box is divided into 2000x2000 tiles to reduce the request size

Bxxxxxxxxx
xxxxxxxxxx
xxxxxxxxxx
xxxxxxxxxx
xxxxxxxxxB
"""


import csv
from datetime import datetime
from pprint import pprint
import json
import requests
from typing import List

TILE_SIDE = 2000

# Roughly Warsaw box coordinates
BOUND_UP = (7489046.2903, 5801540.5856)
BOUND_DOWN = (7518990.0477, 5774703.9076)


def fix_json(reader) -> str:
    print('Fixing json')
    data = reader.replace('id:', '"id": ')
    data = data.replace('name:', '"name": ')
    data = data.replace('gtype:', '"gtype": ')
    data = data.replace('imgurl:', '"imgurl": ')
    data = data.replace('x:', '"x": ')
    data = data.replace(',y:', ',"y": ')
    data = data.replace('width:', '"width": ')
    data = data.replace('height:', '"height": ')
    data = data.replace('attrnames:', '"attrnames": ')
    data = data.replace('themeMBR:', '"themeMBR": ')
    data = data.replace('isWholeImg:', '"isWholeImg": ')
    return data


def extract_tree_attributes(name_value: str) -> dict:
    attrs = {}
    field_values = name_value.split('\n')
    for record in field_values:
        record = record.split(': ')
        attrs[record[0]] = record[1]

    return attrs


def parse_tree_data(data: str) -> dict:
    print('Parsing json')
    parsed_data = json.loads(data)
    for tree in parsed_data['foiarray']:
        attrs = extract_tree_attributes(tree['name'])
        tree.update(attrs)
        tree.pop('name')

    return parsed_data


def get_data_chunk(bbox: List) -> str:
    print('Getting data from server')
    url = 'http://mapa.um.warszawa.pl/mapviewer/foi'
    payload = {
        'request': 'getfoi',
        'version': '1.0',
        'bbox': ':'.join(str('{0:.4f}'.format(c)) for c in bbox),
        'width': 1608,
        'height': 581,
        'theme': 'dane_wawa.BOS_ZIELEN_DRZEWA',
        'clickable': 'yes',
        'area': 'yes',
        'dstsrid': '2178',
        'cachefoi': 'yes',
        'aw': 'no',
        'tid': '649_58860',
    }
    pprint(payload)
    response = requests.get(url, params=payload)
    return response.text


def save_to_csv(tree_data: dict, bbox: List) -> None:
    print('Saving csv')
    fieldnames = [
        'Aktualność danych na dzień',
        'Jednostka zarządzająca',
        'Nazwa polska',
        'Nazwa łacińska',
        'Numer inwentaryzacyjny',
        'Obwód pnia w cm',
        'Wysokość w m',
        'gtype',
        'height',
        'id',
        'imgurl',
        'width',
        'x',
        'y',
    ]

    today = datetime.now().strftime('%Y-%m-%d')
    with open(f'data/trees_{today}.csv', 'w') as desc:
        writer = csv.DictWriter(desc, fieldnames=fieldnames)
        writer.writeheader()
        for row in tree_data:
            writer.writerow(row)


def main() -> None:
    data = []
    for long in range(int(BOUND_UP[0]), int(BOUND_DOWN[0]), TILE_SIDE):
        for lat in reversed(range(int(BOUND_DOWN[1]), int(BOUND_UP[1]), TILE_SIDE)):
            bbox = [
                long, lat - TILE_SIDE,
                long + TILE_SIDE, lat
            ]
            bbox = list(map(float, bbox))
            req_data = get_data_chunk(bbox)
            data_str = fix_json(req_data)
            parsed_data = parse_tree_data(data_str)
            data += parsed_data['foiarray']

    save_to_csv(data, [1, ])


if __name__ == '__main__':
    main()
