"""Write to Google Sheets."""

import gspread
import gspread_formatting
import pandas as pd
import time

# suppress SettingWithCopyWarning
import warnings
warnings.filterwarnings('ignore', category=pd.errors.SettingWithCopyWarning)

# local path
localpath = "v2/"

# connect to Google Sheets
sheetkey = "1cua2Ymw3bb1UUPPRtGoniaLr2SMzAUDT5-S_fTkq0SI"
gc = gspread.service_account()
sh = gc.open_by_key(sheetkey)

# read data list
df0 = pd.read_csv(localpath + "list.csv")

def colnum_to_a1(n):
  """Convert column number to A1 notation."""
  div = n
  string = ""
  while div:
    module = (div-1) % 26
    string = chr(65 + module) + string 
    div = (div - module) // 26
  return string

# read data for each country
header0 = ["poll:identifier", "pollster:id", "start_date", "end_date", "n", "middle_date", "sponsor", "days to elections"]
election_types = ["National", "European"]
for c in df0.iterrows():
  country_code = c[1]["country_code"]
  # read data
  print("Reading " + country_code + ".")
  df = pd.read_csv(localpath + "data/" + country_code + ".csv")
  # National vs EU
  for election_type in election_types:
    df1 = df[df["Scope"] == election_type]
    if df1.empty:
      continue
    # get columns after "Precision"
    cols_after_precision = df1.columns.tolist()[df1.columns.tolist().index('Precision')+1:]
    # fill header
    df1['poll:identifier'] = list(range(len(df1), 0, -1))
    df1.rename(columns={"Polling Firm": "pollster:id", "Fieldwork Start": "start_date", "Fieldwork End": "end_date", "Sample Size": "n", "Commissioners": "sponsor"}, inplace=True)
    # calculate middle date
    df1['start_date'] = pd.to_datetime(df1['start_date'])
    df1['end_date'] = pd.to_datetime(df1['end_date'])
    df1['middle_date'] = df1['start_date'] + (df1['end_date'] - df1['start_date']) / 2
    df1['days to elections'] = None
    # revert to excel serial date
    df1["start_date"] = df1["start_date"].apply(lambda x: x.timestamp() / 86400 + 25569)
    df1["end_date"] = df1["end_date"].apply(lambda x: x.timestamp() / 86400 + 25569)
    df1["middle_date"] = df1["middle_date"].apply(lambda x: x.timestamp() / 86400 + 25569)
    # sort data by middle date, newest first
    df1.sort_values(by=['middle_date'], inplace=True, ascending=False)
    df1.fillna('', inplace=True)
    # data
    df2 = df1[cols_after_precision]
    df2 = df2.applymap(lambda x: str(x).replace('%', '') if isinstance(x, str) else x)
    df2 = df2.apply(pd.to_numeric, errors='coerce').fillna(0)
    # sort columns by first and second rows' values, highest first
    if len(df2) > 1:
      df2 = df2.T.sort_values(by=[df2.index[0], df2.index[1]], ascending=False).T
    else:
      df2 = df2.T.sort_values(by=[df2.index[0]], ascending=False).T
    # write to Google Sheets
    election_bit = "" if election_type == "National" else "_" + election_type[0]
    sheetname = country_code + election_bit
    try:
      worksheet = sh.worksheet(sheetname)
    except:
      worksheet = sh.add_worksheet(title=sheetname, rows="100", cols="20")
    worksheet.clear()
    worksheet.update([header0] + df1.loc[:, header0].values.tolist())
    # set column of type iso date
    col = chr(header0.index('start_date') + ord('A'))
    worksheet.format(col + '2:' + col, {'numberFormat': {'type': 'DATE', 'pattern': 'yyyy-mm-dd'}})
    col = chr(header0.index('middle_date') + ord('A'))
    worksheet.format(col + '2:' + col, {'numberFormat': {'type': 'DATE', 'pattern': 'yyyy-mm-dd'}})
    col = chr(header0.index('end_date') + ord('A'))
    worksheet.format(col + '2:' + col, {'numberFormat': {'type': 'DATE', 'pattern': 'yyyy-mm-dd'}})
    # write data
    col = chr(len(header0) + 1 + ord('A'))
    worksheet.update(col + '1', [df2.columns.values.tolist()] + df2.values.tolist())
    # freeze header
    worksheet.freeze(rows=1)
    # resize G Sheets columns width
    last_col = colnum_to_a1(len(header0) + len(df2.columns) + 1)
    gspread_formatting.set_column_width(worksheet, "A:" + last_col , 70)
    # wait to avoid rate limit
    print("Wrote " + sheetname + ". Waiting 10 seconds...")
    time.sleep(10)

# write list of countries
dfc = df0[["country_code", "country_name"]]
dfc['last_updated'] = None
dfc.iloc[0, dfc.columns.get_loc('last_updated')] = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
worksheet = sh.worksheet("list")
worksheet.clear()
worksheet.update([dfc.columns.values.tolist()] + dfc.values.tolist())


print("Done.")