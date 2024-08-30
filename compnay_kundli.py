import requests
import json

# Define the API endpoint and necessary headers
API_ENDPOINT = "https://api.gatewaydigital.ai/v1/workflows/run"  # Replace with the actual endpoint
BEARER_TOKEN = "E8fjPD4q50beEbKD"  # Replace with your actual bearer token

def scrape_company_data(company_url):
    payload = {
        "company_url": company_url
    }
    headers = {
        'Authorization': f'Bearer {BEARER_TOKEN}',
        'Content-Type': 'application/json'
    }

    response = requests.post(API_ENDPOINT, json=payload, headers=headers)

    if response.status_code == 200:
        scraped_data = response.json()
        return scraped_data
    else:
        print(f"Failed to scrape data. Status code: {response.status_code}, Response: {response.text}")
        return None

if __name__ == '__main__':
    company_url = "https://unless.com"  # Replace with the actual company URL
    scraped_data = scrape_company_data(company_url)

    if scraped_data:
        print("Scraped Data:")
        print(json.dumps(scraped_data, indent=4))  # Pretty print the JSON data
    else:
        print("No data scraped.")




