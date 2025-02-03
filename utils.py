import requests
import os
def start_download(url):
    # Make a web request to https://getthis.stream/api/v1/download
    # with the url as the body
    # return the id of the download
    response = requests.post('https://getthis.stream/api/v1/download', json={'url': url}, headers={'X-Api-Key': os.getenv('AUTH_TOKEN')})
    return response.json()['id']

