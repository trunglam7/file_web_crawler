import os
import requests
from bs4 import BeautifulSoup
from zipfile import ZipFile
from urllib.parse import urljoin, urlparse
import time

# Constants
DELAY = 4  # Delay between requests (in seconds)

visited_urls = set()
file_data = []

# Delay function
def delay_request():
    time.sleep(DELAY)

# Crawl function
def crawl(url, base_url):

    visited_urls.add(url)
    print(f"Crawling: {url} (Visited: {len(visited_urls)}, Files: {len(file_data)})")

    try:
        delay_request()
        response = requests.get(url)
        response.raise_for_status()  # Raise error for bad responses

        if 'text/html' in response.headers['Content-Type']:
            soup = BeautifulSoup(response.text, 'html.parser')
            links = soup.find_all('a')

            for link in links:
                href = link.get('href')
                if href:
                    href = urljoin(base_url, href)
                    if href.startswith(base_url) and href not in visited_urls:
                        crawl(href, base_url)
        else:
            filename = os.path.basename(urlparse(url).path)
            if filename:
                file_data.append({'filename': filename, 'url': url})
    except Exception as e:
        print(f"Error crawling {url}: {e}")

# Download function for files
def download_files():
    for file in file_data:
        try:
            response = requests.get(file['url'])
            response.raise_for_status()
            with open(file['filename'], 'wb') as f:
                f.write(response.content)
            print(f"Downloaded: {file['filename']}")
        except Exception as e:
            print(f"Error downloading {file['url']}: {e}")

# Create ZIP file from downloaded files
def create_zip(file_data):
    zip_filename = "crawled_files.zip"
    with ZipFile(zip_filename, 'w') as zipf:
        for file in file_data:
            if os.path.exists(file['filename']):
                zipf.write(file['filename'], os.path.basename(file['filename']))
                os.remove(file['filename'])  # Remove the downloaded file after zipping
            else:
                print(f"Warning: File not found, skipping: {file['filename']}")
    print(f"ZIP file created: {zip_filename}")

# Main function
def main(url):
    base_url = urlparse(url).scheme + "://" + urlparse(url).hostname
    print(f"Starting crawl on {url}")

    crawl(url, base_url)
    if file_data:
        download_files()
        create_zip()
        print("Crawl complete, ZIP file is ready for download.")
    else:
        print("No files found during crawling.")

if __name__ == "__main__":
    user_url = input("Enter the URL to crawl: ")
    main(user_url)
