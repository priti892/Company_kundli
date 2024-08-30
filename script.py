import requests
from bs4 import BeautifulSoup
import json

# Cohere API details
COHERE_API_ENDPOINT = "https://api.cohere.ai/v1/llm/completions"
COHERE_API_KEY = "your-cohere-api-key"  # Replace with your actual API key

def fetch_webpage(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f"Error fetching the webpage: {e}")
        return None

def extract_links(html_content, base_url):
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        if not link.startswith(('http', 'https')):
            link = requests.compat.urljoin(base_url, link)
        links.add(link)
    return links

def extract_with_llm(content, query):
    payload = {
        "model": "large",
        "prompt": query + "\n" + content,
        "max_tokens": 300,
        "temperature": 0.7
    }
    headers = {
        'Authorization': f'Bearer {COHERE_API_KEY}',
        'Content-Type': 'application/json'
    }
    response = requests.post(COHERE_API_ENDPOINT, json=payload, headers=headers)
    if response.status_code == 200:
        result = response.json()
        return result.get('choices', [{}])[0].get('text', 'No data extracted')
    else:
        print(f"Failed to extract data. Status code: {response.status_code}, Response: {response.text}")
        return None

def main():
    base_url = "https://www.unless.com"  # Replace with the main URL
    html_content = fetch_webpage(base_url)

    if html_content:
        links = extract_links(html_content, base_url)
        print(f"Found {len(links)} links.")
        print(links)
        data_dict = {}
        for link in links:
            page_content = fetch_webpage(link)
            if page_content:
                # Define queries for LLM extraction
                queries = {
                    "summary": "Extract a summary of the business.",
                    "services": "List the services provided by the company.",
                    "leadership": "Provide the names and roles of all leadership members.",
                    "contact_info": "Extract contact information.",
                    "headquarters": "Extract the headquarters location of the company.",
                    "clients": "List the top 10 current clients.",
                    "social_media": "Provide the company's social media handles.",
                    "established_year": "Extract the year the company was established.",
                    "ai_enhancement": "Describe any AI enhancements.",
                    "revenue": "Extract the company's annual revenue.",
                    "competitors": "List the top competitors of the company."
                }

                extracted_data = {}
                for key, query in queries.items():
                    extracted_data[key] = extract_with_llm(page_content, query)

                data_dict[link] = extracted_data

        # Print or save the compiled data
        print(json.dumps(data_dict, indent=4))

if __name__ == '__main__':
    main()
