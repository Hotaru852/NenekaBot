import requests

SHEET_ID = '1JjK7Ws4gfzKChRs5ueoxEZVN5SXK10nhDC1-nbm0NUs'
GID = '303232073'

url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&id={SHEET_ID}&gid={GID}"
response = requests.get(url)
print(response.status_code)