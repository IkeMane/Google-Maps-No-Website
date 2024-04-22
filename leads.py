import requests
import time
import csv
import os
from dotenv import load_dotenv

# Constants
load_dotenv()
API_KEY = os.getenv('API_KEY')


def get_coordinates(place_name):
    geocode_url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name.replace(' ', '+')}&key={API_KEY}"
    response = requests.get(geocode_url)
    results = response.json().get('results', [])
    if results:
        location = results[0]['geometry']['location']
        return f"{location['lat']},{location['lng']}"
    return None

def user_input():
    types = ["restaurant", "spa", "electrician", "roofing_contractor", "painter", "locksmith", "accounting", "plumber" ]
    print("Please choose a type of business:")
    for i, t in enumerate(types, 1):
        print(f"{i}. {t}")
    choice = int(input("Enter number of your choice (or 0 for all types): "))
    if choice == 0:
        selected_types = types  # Use all types if 0 is selected
    else:
        selected_types = [types[choice - 1]]  # Use selected type

    place_name = input("Enter the name of the place (e.g., 'Columbia, MO'): ")
    radius = input("Enter the distance you would like to search (in miles): ")
    radius = int(radius) * 1609.34  # Convert miles to meters
    website_search = int(input("Search for places without websites (1 for yes, 0 for no): "))
    return place_name, radius, selected_types, website_search == 1



def build_url(location, radius, business_type=None, next_page_token=None):
    base_url = f'https://maps.googleapis.com/maps/api/place/nearbysearch/json?location={location}&radius={radius}&key={API_KEY}'
    if business_type:
        base_url += f'&type={business_type}'
    if next_page_token:
        base_url += f'&pagetoken={next_page_token}'
    return base_url


def get_business_details(place_id, filter_no_website):
    # Expanded fields to include address and types
    details_url = f'https://maps.googleapis.com/maps/api/place/details/json?place_id={place_id}&fields=name,formatted_phone_number,website,formatted_address,types&key={API_KEY}'
    response = requests.get(details_url)
    result = response.json().get('result', {})
    
    # Handling cases based on website filter
    if filter_no_website and 'website' not in result:
        return {
            'name': result['name'],
            'phone': result.get('formatted_phone_number', 'N/A'),
            'address': result.get('formatted_address', 'N/A'),
            'industry': ', '.join(result.get('types', []))  # Joining list of types into a string
        }
    elif not filter_no_website:
        return {
            'name': result['name'],
            'phone': result.get('formatted_phone_number', 'N/A'),
            'website': result.get('website', 'N/A'),
            'address': result.get('formatted_address', 'N/A'),
            'industry': ', '.join(result.get('types', []))
        }
    return None


def find_businesses(location, radius, types, filter_no_website):
    businesses = []
    for business_type in types:  # Loop through a list of business types
        next_page_token = None
        while True:
            url = build_url(location, radius, business_type, next_page_token)
            response = requests.get(url)
            json_response = response.json()

            if 'results' not in json_response:
                break

            for result in json_response['results']:
                business = get_business_details(result['place_id'], filter_no_website)
                if business:
                    businesses.append(business)

            next_page_token = json_response.get('next_page_token')
            if not next_page_token:
                break
            time.sleep(2)  # Respect Google's guidelines to pause briefly between API requests
    return businesses

def write_to_csv(businesses, filename='businesses.csv'):
    # Expanded fieldnames to include address and industry
    fieldnames = ['name', 'phone', 'website', 'address', 'industry']
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for business in businesses:
            # Adjust the writerow call to handle potential absence of 'website'
            writer.writerow({
                'name': business['name'],
                'phone': business['phone'],
                'website': business.get('website', 'N/A'),  # Default to 'N/A' if no website
                'address': business['address'],
                'industry': business['industry']
            })


if __name__ == '__main__':
    place_name, radius, types, filter_no_website = user_input()
    location = get_coordinates(place_name)
    if location:
        businesses = find_businesses(location, radius, types, filter_no_website)
        if businesses:
            write_to_csv(businesses)
            print("Data written to businesses.csv.")
        else:
            print("No businesses found based on your criteria.")
    else:
        print("Failed to find coordinates for the given place name.")
