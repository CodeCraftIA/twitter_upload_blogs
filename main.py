import requests
from bs4 import BeautifulSoup
import os
import time
from apscheduler.schedulers.blocking import BlockingScheduler
import tweepy
from keep_alive import keep_alive
keep_alive()

api_key = os.environ.get('api_key')
api_secret = os.environ.get('api_secret')
bearer_token = repr(os.environ.get('bearer_token'))
access_token = os.environ.get('access_token')
access_token_secret = os.environ.get('access_token_secret')


def read_titles_from_file(filename):
    titles_set = set()
    try:
        with open(filename, 'r') as file:
            for line in file:
                titles_set.add(line.strip())
    except FileNotFoundError:
        pass  # If file not found, return an empty set
    return titles_set

def write_titles_to_file(titles_set, filename):
    with open(filename, 'w') as file:
        for title in titles_set:
            file.write(f"{title}\n")


def scrape():
    global available_set
    cur_url = "https://tsboi.com/"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
    response = requests.get(cur_url, headers=headers)

    if not response.ok:
        print('Status Code:', response.status_code)
        #raise Exception('Failed to fetch')
        return
    soup = BeautifulSoup(response.text, 'html.parser')
    a_tags = soup.find_all('a', class_="title-text")
    for tag in a_tags:
        available_set.add((tag.text.strip(), tag.get('href')))
    



def main_function():
    global available_set
    available_set = set()
    scrape()
    # Load previous data
    previous_available_titles = read_titles_from_file('last_articles.txt')
    
    # Extract titles from current sets
    current_available_titles = {title for title, href in available_set}
    
    # Find new products, restocked products, and newly sold-out products
    new_products = current_available_titles - previous_available_titles
    
    client = tweepy.Client(bearer_token, api_key, api_secret, access_token, access_token_secret)
    auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_token_secret)
    api = tweepy.API(auth)


    # Print changes for potential Twitter updates
    print("New Articles:")
    for title in new_products:
        product = next(item for item in available_set if item[0] == title)
        print(product)
        try:
            message = title + "\n" + product[1]
            #api.update_status(data_str)
            client.create_tweet(text = message)
            print("Tweeted successfully!")
        except Exception as e:
            print("Error during tweeting:", e)
        time.sleep(10)
    
    # Combine current and previous titles
    all_titles = current_available_titles.union(previous_available_titles)

    # Write the combined titles to the file
    write_titles_to_file(all_titles, 'last_articles.txt')

if __name__ == '__main__':
    main_function()
    scheduler = BlockingScheduler()
    scheduler.add_job(main_function, 'interval', minutes=300)
    scheduler.start()
