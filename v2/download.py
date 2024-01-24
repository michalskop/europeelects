"""Download data from EuropeElects.eu."""

import csv
import requests
import requests_html
import urllib3.exceptions
import time

# local path
localpath = "v2/"

# overview table url
url0 = "https://europeelects.eu/data/"

# get the table
session = requests_html.HTMLSession()
r = session.get(url0)
try:
  r.html.render()
except urllib3.exceptions.InvalidChunkLength as e:
  r.close()
  raise Exception(f'InvalidChunkLength exception occurred: {e}')

if r.status_code != 200:
  raise Exception("Could not download data.")

# select table
table = r.html.find("figure[class=wp-block-table]")[0].find("table")[0]

# get data
data = []
for row in table.find('tr'):
  cells = row.find('td')
  if cells:
    country = cells[0].find('a', first=True)
    country_name = country.text if country else None
    country_link = country.attrs['href'] if country else None
    try:
      data_link = cells[1].find('a', first=True).attrs['href']
      country_code = data_link.split("/")[-1].split(".")[0]
    except:
      data_link = None
    if country_name and country_link and data_link:
      data.append({
        "country_code": country_code,
        "country_name": country_name, 
        "country_link": country_link,
        "data_link": data_link
      })

# write data to csv
with open(localpath + "list.csv", "w") as f:
  writer = csv.DictWriter(f, fieldnames=data[0].keys())
  writer.writeheader()
  writer.writerows(data)

# download data
try:
  for d in data:
    r = requests.get(d["data_link"])
    if r.status_code == 200:
      with open(localpath + "data/" + d["country_code"] + ".csv", "wb") as f:
        f.write(r.content)
    time.sleep(1)
except Exception as e:
  r.close()
  raise Exception(f'An exception occurred during the download: {e}')