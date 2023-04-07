import requests
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

#pull API key from txt file
API_KEY = open("api_key.txt", "r").read()
LOCATION = '37.205066, -93.285341'  # Approximate center of Lake of the Ozarks
RADIUS = '50000'  # Search within a 50 km radius
TYPE = 'lodging' #https://developers.google.com/maps/documentation/places/web-service/supported_types
KEYWORD = ''

def find_businesses_without_website():
    businesses = []
    next_page_token = None

    while True:
        url = build_url(next_page_token)
        response = requests.get(url)
        json_response = response.json()

        if 'results' not in json_response:
            break

        for result in json_response['results']:
            place_id = result['place_id']
            business = get_business_details(place_id)
            if business:
                businesses.append(business)

        if 'next_page_token' not in json_response:
            break

        next_page_token = json_response['next_page_token']
        time.sleep(2)  # Wait for the next page token to be valid

    return businesses

def build_url(next_page_token=None):
    base_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={LOCATION}&radius={RADIUS}&type={TYPE}&keyword={KEYWORD}&key={API_KEY}'

    if next_page_token:
        base_url += f'&pagetoken={next_page_token}'

    return base_url

def get_business_details(place_id):
    details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website&key={API_KEY}'
    response = requests.get(details_url)
    json_response = response.json()

    if 'result' in json_response:
        result = json_response['result']
        if 'website' not in result:
            business = {
                'name': result['name'],
                'phone': result['formatted_phone_number'] if 'formatted_phone_number' in result else 'N/A'
            }
            return business
    return None

if __name__ == '__main__':
    businesses = find_businesses_without_website()

    if not businesses:
        print("No businesses without a website found.")
    else:
        for business in businesses:
            print(f"Business Name: {business['name']}, Phone Number: {business['phone']}")

def get_credentials():
    from google.oauth2 import service_account

    # Replace the string with the path to your service account key JSON file
    key_path = "single-azimuth-383002-bc27fcf42784.json"

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = service_account.Credentials.from_service_account_file(key_path, scopes=scopes)
    return creds

def share_google_sheet_with_email(sheet_id, email, role, credentials):
    service = build('drive', 'v3', credentials=credentials)
    user_permission = {
        'type': 'user',
        'role': role,
        'emailAddress': email
    }
    request = service.permissions().create(
        fileId=sheet_id,
        body=user_permission,
        fields='id'
    )
    request.execute()


def create_sheet(sheet_name, credentials):
    try:
        service = build('sheets', 'v4', credentials=credentials)
        spreadsheet = {
            'properties': {
                'title': sheet_name
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                    fields='spreadsheetId').execute()
        
        print(f'Spreadsheet ID: {spreadsheet.get("spreadsheetId")}')

        your_email_address = open("personal_email.txt","r").read()  # Replace with your actual email address
        share_google_sheet_with_email(spreadsheet['spreadsheetId'], your_email_address, 'writer', credentials)

  
        return spreadsheet.get('spreadsheetId')
    except HttpError as error:
        print(f'An error occurred: {error}')
        return None


def write_to_sheet(sheet_id, data, credentials):
    try:
        service = build('sheets', 'v4', credentials=credentials)
        values = []
        for item in data:
            values.append([item['name'], item['phone']])
        
        body = {
            'values': values
        }
        range_name = 'A:B'
        result = service.spreadsheets().values().append(
            spreadsheetId=sheet_id, range=range_name,
            valueInputOption='RAW', insertDataOption='INSERT_ROWS', body=body).execute()
        print(f'{result.get("updates").get("updatedCells")} cells updated.')
    except HttpError as error:
        print(f'An error occurred: {error}')


if __name__ == '__main__':
    credentials = get_credentials()
    sheet_name = 'Businesses without Website'
    sheet_id = open("sheet_id.txt", "r").read()
    if sheet_id:
        businesses = find_businesses_without_website()
        if businesses:
            write_to_sheet(sheet_id, businesses, credentials)
            print(f"Results have been written to the Google Sheet '{sheet_name}'.")
        else:
            print("No businesses without a website found.")
    else:
        print("Error creating Google Sheet.")