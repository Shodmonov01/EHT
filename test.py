import gspread
from oauth2client.service_account import ServiceAccountCredentials

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("/home/capma/repo/freelance_projects/EHT/backend/config/keys/credentials.json", scope)

client = gspread.authorize(creds)
sheet = client.open_by_url("https://docs.google.com/spreadsheets/d/1FfooaDunqiVekiudUbfXE9AglxAPsOhvnfQuhERr2Lo/edit")
worksheet = sheet.get_worksheet_by_id(683090842)

print("Sheet title:", worksheet.title)
