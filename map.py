import requests
import time


API_KEY = 'Your_API_Key'
LOCATION = '37.205066, -93.285341'  # Approximate center of Lake of the Ozarks
RADIUS = '50000'  # Search within a 50 km radius
TYPE = 'lawyer'
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
