import os
import requests
import mimetypes
import filetype
from bs4 import BeautifulSoup
from zipfile import ZipFile
from urllib.parse import urljoin, urlparse
import time
import argparse

# Constants
DELAY = 1  # Delay between requests (in seconds)
RESULT_DIR = "result"  # Directory for storing downloaded files

visited_urls = set()
file_data = []

# Delay function
def delay_request():
    time.sleep(DELAY)

# Crawl function
def crawl(url, base_url):
    """Recursively crawls a website, collecting file URLs."""
    visited_urls.add(url)
    print(f"Crawling: {url} (Visited: {len(visited_urls)}, Files: {len(file_data)})")

    try:
        delay_request()
        response = requests.get(url)
        response.raise_for_status()

        if 'text/html' in response.headers.get('Content-Type', ''):
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
            file_data.append({'filename': filename, 'url': url})
    except Exception as e:
        print(f"Error crawling {url}: {e}")

# Download function for files
def download_files():
    """Downloads files and ensures correct extensions."""
    # Create the result directory if it doesn't exist
    if not os.path.exists(RESULT_DIR):
        os.makedirs(RESULT_DIR)

    for file in file_data:
        try:
            response = requests.get(file['url'])
            response.raise_for_status()

            # Try to determine the correct file extension using filetype first
            kind = filetype.guess(response.content)
            if kind:
                extension = kind.extension
            else:
                # If filetype.guess fails, fallback to mimetypes
                content_type = response.headers.get('Content-Type', '')
                extension = mimetypes.guess_extension(content_type) or ''

            # Append extension only if it's missing
            filename = file['filename']
            if extension and not filename.endswith(extension):
                filename += extension

            # Save the file in the result directory
            file_path = os.path.join(RESULT_DIR, filename)
            with open(file_path, 'wb') as f:
                f.write(response.content)

            print(f"Downloaded: {filename}")

            # Update filename in file_data with the full path
            file['filename'] = file_path

        except Exception as e:
            print(f"Error downloading {file['url']}: {e}")

# Create ZIP file from downloaded files
def create_zip():
    """Creates a ZIP file from downloaded files and removes originals."""
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
def main(url, base_url):
    print(f"Starting crawl on {url}")

    crawl(url, base_url)
    if file_data:
        download_files()
        create_zip()
        print("Crawl complete, ZIP file is ready for download.")
    else:
        print("No files found during crawling.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Crawl a website and download its files.")
    parser.add_argument('-u', '--url', type=str, required=True, help="The URL to crawl.")
    parser.add_argument('-b', '--base_url', type=str, help="The base URL to use for relative links (defaults to the URL's scheme + hostname).")
    args = parser.parse_args()

    base_url = args.base_url or urlparse(args.url).scheme + "://" + urlparse(args.url).hostname
    main(args.url, base_url)
