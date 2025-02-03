import csv
import os
import requests
from PIL import Image
import PIL
from io import BytesIO
import json
import wordninja
from tqdm import tqdm
from bs4 import BeautifulSoup
import re
import base64

# Define file paths
CSV_FILE = 'supported-websites.csv'
FAVICONS_DIR = 'favicons'
PNG_DIR = os.path.join('static', 'images', 'favicons')
JSON_FILE = 'favicons.json'

# Create necessary directories if they don't exist
os.makedirs(FAVICONS_DIR, exist_ok=True)
os.makedirs(PNG_DIR, exist_ok=True)

def do_web_search(service_name):
    # set up the request parameters
    params = {
    'api_key': os.getenv('VALUE_SERP_API_KEY'),
    'q': service_name,
    'gl': 'us',
    'hl': 'en',
    'google_domain': 'google.com',
    'include_ai_overview': 'false'
    }
    tqdm.write(f'Searching for {service_name} on Google.')
    # make the http GET request to VALUE SERP
    api_result = requests.get('https://api.valueserp.com/search', params)

    json = api_result.json()
    json = json['organic_results']
    for result in json:
        if result['link']:
            if "youtube.com" in result['link'] or "youtu.be" in result['link'] or "twitch.tv" in result['link'] or "tiktok.com" in result['link'] or "instagram.com" in result['link'] or "facebook.com" in result['link'] or "twitter.com" in result['link'] or "linkedin.com" in result['link'] or "pinterest.com" in result['link'] or "reddit.com" in result['link'] or "discord.com" in result['link'] or "snapchat.com" in result['link'] or "whatsapp.com" in result['link'] or "spotify.com" in result['link'] or "soundcloud.com" in result['link'] or "bandcamp.com" in result['link'] or "soundcloud.com" in result['link'] or "bandcamp.com" in result['link'] or "soundcloud.com" in result['link'] or "bandcamp.com" in result['link']:
                continue
            else:
                json = result
                break
    response = {
        "service": service_name,
        "website": json['domain'],
        "title": json['title']
    }
    tqdm.write(f'Found {service_name} on Google. Website: {response["website"]}. Title: {response["title"]}')
    return response

# Function to capitalize the first letter of each word using wordninja
def generate_title(service_name, html_title=None):
    # Attempt to split the service name using wordninja
    words = wordninja.split(service_name)
    if words:
        capitalized_words = [word.capitalize() for word in words]
        title = ' '.join(capitalized_words)
        # If title is too short or doesn't make sense, fallback to HTML title
        if len(title) < 3 or title.lower() in ['abc', 'bbc', 'cnn']:  # Example condition
            if html_title:
                title = html_title
    else:
        # Fallback to HTML title if wordninja fails
        title = html_title if html_title else service_name.capitalize()
    return title

# Function to parse data URI
def parse_data_uri(data_uri):
    """
    Parses a data URI and returns the MIME type and decoded data.
    """
    try:
        header, encoded = data_uri.split(',', 1)
        mime_match = re.match(r'data:(image/[^;]+);base64', header, re.I)
        if not mime_match:
            return None, None
        mime_type = mime_match.group(1).lower()
        decoded_data = base64.b64decode(encoded)
        return mime_type, decoded_data
    except Exception:
        return None, None

# Lists to store JSON data
json_data = []
service_data = []
# Read the CSV file
with open(CSV_FILE, 'r', newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile)
    # Wrap the reader with tqdm for progress bar
    for row in tqdm(reader, desc="Processing CSV", unit="service"):
        service = row['filename']
        website = row['website'] + '.com'  # Append .com as per instruction
        if os.path.exists(os.path.join(PNG_DIR, f'favicon-{service}.png')):
            continue
        service_data.append({
            "service": service,
            "website": website
        })

for row in tqdm(service_data, desc="Processing Services", unit="service"):
    service = row['service']
    website = row['website']

    tqdm.write(f'Processing service: {service}, website: {website}')

    try:
        ponzi = False
        soup = None
        # Attempt to visit the website
        try: 
            tqdm.write(f'Fetching website {website}')
            response = requests.get(f'https://{website}', timeout=3)
            tqdm.write(f'Website {website} is reachable. Status Code: {response.status_code}')
        except Exception as e:
            ponzi = True
            tqdm.write(f'Error fetching website {website}. Ponzi\'ing.')

        if ponzi == False and response.status_code != 200:
            ponzi = True

        if ponzi == True:
            response = do_web_search(service)
        
        success = False
        success_title = False
        try: 
            if response['website']: 
                success = True 
                success_title = True
                website = response['website'].replace("https://", "").replace("http://", "").replace("www.", "").replace("/", "").strip()
        except:
            pass
        try:
            if response.status_code == 200:
                success = True
        except:
            pass
        

        if success:
            if success_title:
                if "-" in response['title']:
                    html_title = response['title'][0:response['title'].index('-')].strip()
                elif "|" in response['title']:
                    html_title = response['title'][0:response['title'].index('|')].strip()
                else:
                    html_title = response['title']
            try:
                if success_title:
                    try:
                        response = requests.get(f'https://{website}', timeout=3)
                        tqdm.write(f'Website {website} is reachable.')
                    except Exception as e:
                        tqdm.write(f'Error fetching website {website}: {e}. Skipping.')
                        continue

                soup = BeautifulSoup(response.text, 'html.parser')
                if not success_title:
                    html_title = soup.title.string.strip() if soup.title and soup.title.string else None
            except Exception as e:
                tqdm.write(f'Error parsing HTML for {service}: {e}')
                soup = None

            if html_title == None:
                response = do_web_search(service)
                if response['title']:
                    if "-" in response['title']:
                        html_title = response['title'][0:response['title'].index('-')].strip()
                    elif "|" in response['title']:
                        html_title = response['title'][0:response['title'].index('|')].strip()
                    else:
                        html_title = response['title']
                else:
                    html_title = None

            # Attempt to retrieve favicon using <link rel="icon"> or similar in HTML
            favicon_url = None
            if soup:
                tqdm.write(f'Parsing HTML for {service}')
                # Look for various possible rel values
                icon_link = soup.find('link', rel=lambda x: x and 'icon' in x.lower())
                
                if not html_title:
                    if soup.title and soup.title.string:
                        html_title = soup.title.string.strip() 

                # Generate title
                if html_title:  
                    title = html_title
                else:
                    title = generate_title(service)

                if icon_link and icon_link.get('href'):
                    favicon_href = icon_link['href'].strip()
                    # Check if favicon_href is a data URI
                    if favicon_href.startswith('data:'):
                        mime_type, decoded_data = parse_data_uri(favicon_href)
                        if mime_type and decoded_data:
                            if mime_type != 'image/png':
                                # Convert to PNG
                                try:
                                    img = Image.open(BytesIO(decoded_data))
                                    img = img.convert('RGBA')
                                    img = img.resize((32, 32), PIL.Image.LANCZOS)
                                    png_filename = f'favicon-{service}.png'
                                    png_path = os.path.join(PNG_DIR, png_filename)
                                    img.save(png_path, format='PNG')
                                    tqdm.write(f'Converted base64 favicon to PNG for {service}.')
                                    
                                    # Append data to JSON list
                                    json_data.append({
                                        'service': service,
                                        'website': website,
                                        'favicon': png_path.replace('\\', '/'),  # For cross-platform compatibility
                                        'title': title
                                    })
                                    continue  # Move to next service
                                except Exception as e:
                                    tqdm.write(f'Error converting base64 favicon to PNG for {service}: {e}. Skipping.')
                                    continue  # Skip to next service
                            else:
                                # It's a PNG, decode and save
                                try:
                                    img = Image.open(BytesIO(decoded_data))
                                    img = img.convert('RGBA')
                                    img = img.resize((32, 32), PIL.Image.LANCZOS)
                                    png_filename = f'favicon-{service}.png'
                                    png_path = os.path.join(PNG_DIR, png_filename)
                                    img.save(png_path, format='PNG')
                                    tqdm.write(f'Decoded base64 PNG favicon for {service}.')
                                    
                                    # Append data to JSON list
                                    json_data.append({
                                        'service': service,
                                        'website': website,
                                        'favicon': png_path.replace('\\', '/'),  # For cross-platform compatibility
                                        'title': title
                                    })
                                    continue  # Move to next service
                                except Exception as e:
                                    tqdm.write(f'Error decoding base64 PNG favicon for {service}: {e}. Skipping.')
                                    continue  # Skip to next service
                    else:
                        # It's a URL, construct absolute URL if necessary
                        if favicon_href.startswith('http'):
                            favicon_url = favicon_href
                        else:
                            favicon_url = requests.compat.urljoin(f'https://{website}', favicon_href)
                else:
                    tqdm.write(f'No favicon found in HTML for {service} at {website}.')

            # If favicon_url is still not set, fallback to /favicon.ico
            if not favicon_url:
                favicon_url = f'https://{website}/favicon.ico'

            # Now, handle favicon_url (which is a URL)
            try:
                tqdm.write(f'Fetching favicon from {favicon_url}')
                favicon_response = requests.get(favicon_url, timeout=10)
                tqdm.write(f'Favicon fetched from {favicon_url}. Response Code: {favicon_response.status_code}')
                if favicon_response.status_code == 200:
                    # Check if the response is a data URI (unlikely, but for completeness)
                    if favicon_url.startswith('data:'):
                        tqdm.write(f'Favicon is a data URI for {service} at {website}.')
                        mime_type, decoded_data = parse_data_uri(favicon_url)
                        if mime_type and decoded_data:
                            if mime_type != 'image/png':
                                # Convert to PNG
                                try:
                                    tqdm.write(f'Converting data URI favicon to PNG for {service}.')
                                    img = Image.open(BytesIO(decoded_data))
                                    img = img.convert('RGBA')
                                    img = img.resize((32, 32), PIL.Image.LANCZOS)
                                    png_filename = f'favicon-{service}.png'
                                    png_path = os.path.join(PNG_DIR, png_filename)
                                    img.save(png_path, format='PNG')
                                    tqdm.write(f'Converted data URI favicon to PNG for {service}.')
                                    
                                    # Generate title
                                    title = generate_title(service, html_title)
                                    
                                    # Append data to JSON list
                                    json_data.append({
                                        'service': service,
                                        'website': website,
                                        'favicon': png_path.replace('\\', '/'),  # For cross-platform compatibility
                                        'title': title
                                    })
                                    continue  # Move to next service
                                except Exception as e:
                                    tqdm.write(f'Error converting data URI favicon to PNG for {service}: {e}. Skipping.')
                                    continue  # Skip to next service
                            else:
                                # It's a PNG, decode and save
                                try:
                                    tqdm.write(f'Decoding data URI PNG favicon for {service}.')
                                    img = Image.open(BytesIO(decoded_data))
                                    img = img.convert('RGBA')
                                    img = img.resize((32, 32), PIL.Image.LANCZOS)
                                    png_filename = f'favicon-{service}.png'
                                    png_path = os.path.join(PNG_DIR, png_filename)
                                    img.save(png_path, format='PNG')
                                    tqdm.write(f'Decoded data URI PNG favicon for {service}.')
                                    
                                    # Generate title
                                    title = generate_title(service, html_title)
                                    
                                    # Append data to JSON list
                                    json_data.append({
                                        'service': service,
                                        'website': website,
                                        'favicon': png_path.replace('\\', '/'),  # For cross-platform compatibility
                                        'title': title
                                    })
                                    continue  # Move to next service
                                except Exception as e:
                                    tqdm.write(f'Error decoding data URI PNG favicon for {service}: {e}. Skipping.')
                                    continue  # Skip to next service

                    # Check MIME type
                    content_type = favicon_response.headers.get('Content-Type', '').lower()
                    if 'image/x-icon' in content_type or 'image/vnd.microsoft.icon' in content_type or 'image/jpeg' in content_type or 'stream' in content_type:
                        tqdm.write(f'Favicon MIME type for {service} is valid ({content_type}).')
                        # Save the .ico file
                        ico_path = os.path.join(FAVICONS_DIR, f'{service}.ico')
                        with open(ico_path, 'wb') as ico_file:
                            ico_file.write(favicon_response.content)
                        tqdm.write(f'Downloaded favicon.ico for {service}.')

                        # Additional verification: Attempt to open the .ico file with Pillow
                        try:
                            with Image.open(ico_path) as img:
                                tqdm.write(f'Verifying favicon.ico for {service}.')
                                img.verify()  # Verify that it's an image

                            tqdm.write(f'Verified favicon.ico for {service}.')
                            # Re-open to proceed with conversion
                            with Image.open(ico_path) as img:
                                tqdm.write(f'Converting favicon.ico to PNG for {service}.')
                                img = img.convert('RGBA')
                                img = img.resize((32, 32), PIL.Image.LANCZOS)
                                png_filename = f'favicon-{service}.png'
                                png_path = os.path.join(PNG_DIR, png_filename)
                                img.save(png_path, format='PNG')
                            tqdm.write(f'Converted favicon.ico to PNG for {service}.')

                            # Append data to JSON list
                            json_data.append({
                                'service': service,
                                'website': website,
                                'favicon': png_path.replace('\\', '/'),  # For cross-platform compatibility
                                'title': title
                            })

                        except Exception as e:
                            tqdm.write(f'Invalid .ico file for {service}: {e}. Deleting file and skipping.')
                            os.remove(ico_path)  # Delete the invalid .ico file
                            continue  # Skip to the next service

                    elif 'image/png' in content_type:
                        tqdm.write(f'Favicon MIME type for {service} is PNG ({content_type}).')
                        # Save the PNG file directly
                        try:
                            img = Image.open(BytesIO(favicon_response.content))
                            img = img.convert('RGBA')
                            img = img.resize((32, 32), PIL.Image.LANCZOS)
                            png_filename = f'favicon-{service}.png'
                            png_path = os.path.join(PNG_DIR, png_filename)
                            img.save(png_path, format='PNG')
                            tqdm.write(f'Downloaded and saved PNG favicon for {service}.')

                            # Generate title
                            title = generate_title(service, html_title)

                            # Append data to JSON list
                            json_data.append({
                                'service': service,
                                'website': website,
                                'favicon': png_path.replace('\\', '/'),  # For cross-platform compatibility
                                'title': title
                            })

                        except Exception as e:
                            tqdm.write(f'Error processing PNG favicon for {service}: {e}. Skipping.')
                            continue  # Skip to the next service

                    else:
                        tqdm.write(f'Unsupported MIME type for favicon of {service}: {content_type}. Skipping.')
                        continue  # Skip to the next service

            except requests.RequestException as e:
                tqdm.write(f'Error fetching favicon for {service} from {favicon_url}: {e}')
                continue  # Skip to the next service

        else:
            tqdm.write(f'Website {website} returned status code {response.status_code}. Skipping.')
            continue  # Skip to the next entry if the website is not reachable

    except requests.RequestException as e:
        tqdm.write(f'Error accessing website {website}: {e}. Skipping.')
        continue  # Skip to the next entry if the website is not reachable

# Save the JSON data to a file
with open(JSON_FILE, 'w', encoding='utf-8') as jsonfile:
    json.dump(json_data, jsonfile, indent=4)
    tqdm.write(f'JSON data saved to {JSON_FILE}.')

tqdm.write('Script completed.')
