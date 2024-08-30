from flask import Flask, request, jsonify
import requests
from bs4 import BeautifulSoup
import cohere
import concurrent.futures
import time

# Cohere API details
COHERE_API_KEY = "7VCjBKUfyn1KNX7bNaEEkMM3N8YbIRH4NXwd7AU8"

# Initialize the Cohere client
co = cohere.Client(COHERE_API_KEY)

app = Flask(__name__)

# Keywords that are likely to be in URLs with relevant information
RELEVANT_URL_KEYWORDS = [
    "contact", "about", "team", "leadership", "services", "pricing",
    "support", "founder", "partners", "clients", "company", "social", "history"
]

def fetch_webpage(url, retries=3):
    """Fetches the HTML content of a webpage with retries."""
    for i in range(retries):
        try:
            response = requests.get(url, timeout=120)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            print(f"Attempt {i+1} - Error fetching the webpage: {e}")
        if i < retries - 1:
            time.sleep(2)
    return None

def extract_links(html_content, base_url):
    """Extracts all sub-URLs from the given HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    links = set()
    for a_tag in soup.find_all('a', href=True):
        link = a_tag['href']
        if link.startswith('mailto:'):
            continue
        if not link.startswith(('http', 'https')):
            link = requests.compat.urljoin(base_url, link)  # Corrected line
        links.add(link)
    return links

def filter_links_by_keywords(links):
    """Filters links based on keywords in the URL."""
    filtered_links = []
    for link in links:
        if any(keyword in link.lower() for keyword in RELEVANT_URL_KEYWORDS):
            filtered_links.append(link)
    return filtered_links

def fetch_and_analyze_content(url):
    """Fetches the content of a URL and analyzes it using LLM."""
    page_content = fetch_webpage(url)
    if page_content:
        soup = BeautifulSoup(page_content, 'html.parser')
        text = soup.get_text(separator="\n")
        return text
    return ""

def analyze_content_with_llm(content):
    """Uses LLM to determine if the content contains relevant company information."""
    prompt = f"""
    The following content is from a webpage. Determine if it contains any information about the company's contact details, team members, leadership, founders, services, pricing, or support.

    Content:
    {content}

    Answer with 'Yes' if the content contains any relevant company information, otherwise 'No'.
    """
    try:
        response = co.generate(
            model="command-xlarge-nightly",
            prompt=prompt,
            max_tokens=50,
            temperature=0.5
        )
        return "Yes" in response.generations[0].text.strip()
    except Exception as e:
        print(f"Error with Cohere API: {e}")
        return False

def filter_relevant_links(links):
    """Filters links based on their content using LLM, with rate limiting."""
    relevant_links = []
    
    def process_link(link):
        content = fetch_and_analyze_content(link)
        result = analyze_content_with_llm(content)
        time.sleep(1)  # Reducing sleep time to speed up
        return link if result else None

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # Increased max workers
        results = executor.map(process_link, links)
        relevant_links = [link for link in results if link]
    
    return relevant_links[:5]  # Reducing the number of relevant links

def scrape_and_compile_content(urls):
    """Fetches and compiles content from a list of URLs."""
    compiled_content = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        contents = executor.map(fetch_webpage, urls)
        for content in contents:
            if content:
                soup = BeautifulSoup(content, 'html.parser')
                compiled_content.append(soup.get_text(separator="\n"))
    
    return "\n\n".join(compiled_content)

def extract_with_llm(content, query):
    """Uses Cohere's LLM to extract specific information from the content."""
    try:
        response = co.generate(
            model="command-xlarge-nightly",
            prompt=query + "\n" + content,
            max_tokens=300,
            temperature=0.5
        )
        return response.generations[0].text.strip() if response.generations else "No data extracted"
    except Exception as e:
        print(f"Error with Cohere API: {e}")
        return "Failed to extract data"

@app.route('/extract-info', methods=['GET'])
def extract_info():
    base_url = request.args.get('url')
    
    if not base_url:
        return jsonify({'error': 'Base URL is required', 'response': 0}), 400

    html_content = fetch_webpage(base_url)

    if html_content:
        links = extract_links(html_content, base_url)
        print(f"Found {len(links)} links.")
        
        # Filter links by keywords in the URL
        filtered_links = filter_links_by_keywords(links)
        print(f"Filtered {len(filtered_links)} links based on URL keywords.")
        
        relevant_links = filter_relevant_links(filtered_links)
        print(f"Selected {len(relevant_links)} relevant links.")
        
        if len(relevant_links) == 0:
            return jsonify({'error': 'No relevant links found', 'response': 0}), 500
        
        # Scrape and compile content from relevant links
        compiled_content = scrape_and_compile_content(relevant_links)
        
        # Define queries for LLM extraction
        queries = {
            "summary": "Extract the summary of the business of 3-4 paragraphs...",
            "services with pricing": "List the services provided by the company with their pricing...",
            "leadership": "Provide the names and roles of all leadership members.",
            "contact_info": "Extract contact information.",
            "headquarters": "Extract all headquarters locations of the company.",
            "clients": "List the top 10 current clients or customers of the company.",
            "social_media": "Provide the company's social media handles.",
            "established_year": "Extract the year the company was established.",
            "AI ENHANCEMENT": "Get AI enhancement for the company."
        }

        # Extract data using Cohere with rate limiting
        data_dict = {}
        try:
            for key, query in queries.items():
                extracted_data = extract_with_llm(compiled_content, query)
                data_dict[key] = extracted_data
                time.sleep(1)  # Reduced delay to speed up process
        except Exception as e:
            print(f"Error extracting data with LLM: {e}")
            return jsonify({'error': 'Failed to extract data', 'response': 0}), 500

        # Return the compiled data as JSON response
        return jsonify(data_dict), 200

    return jsonify({'error': 'Failed to fetch or process the base URL', 'response': 0}), 500

if __name__ == '__main__':
    app.run(host='10.0.2.228', port=5000, debug=True)
