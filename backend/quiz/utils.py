import gspread
from drf_spectacular.utils import extend_schema, OpenApiParameter
from oauth2client.service_account import ServiceAccountCredentials
import os
from django.conf import settings


def get_google_sheet():
            scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
            creds_path = os.path.join(settings.BASE_DIR, 'config', 'keys', 'credentials.json')
            creds = ServiceAccountCredentials.from_json_keyfile_name(creds_path, scope)
            client = gspread.authorize(creds)

            # Откройте Google Sheet по URL
            sheet_url = "https://docs.google.com/spreadsheets/d/1FfooaDunqiVekiudUbfXE9AglxAPsOhvnfQuhERr2Lo/"
            sheet = client.open_by_url(sheet_url).sheet1

            return sheet
