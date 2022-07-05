"""Download / backup data."""

import csv
import requests

with open("list.csv") as fin:
  csvr = csv.DictReader(fin)
  for row in csvr:
    url = "https://filipvanlaenen.github.io/eopaod/" + row['code'].strip() + ".csv"
    r = requests.get(url)
    with open("data_original/" + row['code'] + ".csv", "w") as fout:
      fout.write(r.text)
