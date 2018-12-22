# -*- coding: utf-8 -*-

"""
Copyright 2015 Randal S. Olson

This file is part of the reddit Twitter Bot library.

The reddit Twitter Bot library is free software: you can redistribute it and/or
modify it under the terms of the GNU General Public License as published by the
Free Software Foundation, either version 3 of the License, or (at your option)
any later version.

The reddit Twitter Bot library is distributed in the hope that it will be
useful, but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
License for more details. You should have received a copy of the GNU General
Public License along with the reddit Twitter Bot library.
If not, see http://www.gnu.org/licenses/.
"""

import praw
import json
import requests
import tweepy
import time
import os
import urllib.parse
from glob import glob

# Place your Twitter API keys here
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Place your reddit API keys here
CLIENT_ID = ''
CLIENT_SECRET = ''
USER_AGENT = ''

# Place the subreddit you want to look up posts from here
SUBREDDIT_TO_MONITOR = ''

# Place the name of the folder where the images are downloaded
IMAGE_DIR = 'img'

# Place the name of the file to store the IDs of posts that have been posted
POSTED_CACHE = 'posted_posts.txt'

# Place the string you want to add at the end of your tweets (can be empty)
TWEET_SUFFIX = ' #elitedangerous'

# Place the maximum length for a tweet
TWEET_MAX_LEN = 280

# Place the time you want to wait between each tweets (in seconds)
DELAY_BETWEEN_TWEETS = 30

# Place the lengths of t.co links (cf https://dev.twitter.com/overview/t.co)
T_CO_LINKS_LEN = 24


def setup_connection_reddit(subreddit):
    """Creates a read-only connection to the reddit API."""
    print('[bot] Setting up connection with reddit')
    reddit_api = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent=USER_AGENT)

    return reddit_api.subreddit(subreddit)


def tweet_creator(subreddit_info):
    """Looks up posts from reddit and shortens the URLs to them."""
    post_dict = {}
    post_ids = []

    print('[bot] Getting posts from reddit')

    # You can use the following methods on the "front" object to get posts from reddit:
    #   - front.top(): gets the most-upvoted posts (ignoring post age)
    #   - front.hot(): gets the most-upvoted posts (taking post age into account)
    #   - front.new(): gets the newest posts
    #   - front.rising(): gets rising posts
    #
    # "limit" tells the API the maximum number of posts to look up

    for submission in subreddit_info.front.hot(limit=5):
        if not already_tweeted(submission.id):
            # This stores a link to the reddit post itself
            # If you want to link to what the post is linking to instead, use
            # "submission.url" instead of "submission.permalink"
            post_dict[submission.title] = {}
            post = post_dict[submission.title]
            post['link'] = submission.permalink

            # Store the url the post points to (if any)
            # If it's an imgur URL, it will later be downloaded and uploaded alongside the tweet
            post['img_path'] = get_image(submission.url)

            post_ids.append(submission.id)
        else:
            print('[bot] Already tweeted: {}'.format(str(submission)))

    return post_dict, post_ids


def already_tweeted(post_id):
    """Checks if the reddit Twitter bot has already tweeted a post."""
    found = False
    with open(POSTED_CACHE, 'r') as in_file:
        for line in in_file:
            if post_id in line:
                found = True
                break
    return found


def strip_title(title, num_characters):
    """Shortens the title of the post to the 140 character limit."""
    # How much you strip from the title depends on how much extra text
    # (URLs, hashtags, etc.) that you add to the tweet
    # Note: it is annoying but some short urls like "data.gov" will be
    # replaced by longer URLs by twitter. Long term solution could be to
    # use urllib.parse to detect those.
    if len(title) <= num_characters:
        return title
    else:
        return title[:num_characters - 1] + '…'


def get_image(img_url):
    """Downloads i.imgur.com and i.redd.it images that reddit posts may point to."""
    if ('imgur.com' in img_url) or ('i.redd.it' in img_url):
        file_name = os.path.basename(urllib.parse.urlsplit(img_url).path)
        img_path = IMAGE_DIR + '/' + file_name
        print('[bot] Downloading image at URL ' + img_url + ' to ' + img_path)
        resp = requests.get(img_url, stream=True)
        if resp.status_code == 200:
            with open(img_path, 'wb') as image_file:
                for chunk in resp:
                    image_file.write(chunk)
            # Return the path of the image, which is always the same since we just overwrite images
            return img_path
        else:
            print('[bot] Image failed to download. Status code: ' + resp.status_code)
    else:
        print('[bot] Post doesn\'t point to an i.imgur.com or i.redd.it link')
    return ''


def tweeter(post_dict, post_ids):
    """Tweets all of the selected reddit posts."""
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    for post, post_id in zip(post_dict, post_ids):
        img_path = post_dict[post]['img_path']

        extra_text = ' ' + post_dict[post]['link'] + TWEET_SUFFIX
        extra_text_len = 1 + T_CO_LINKS_LEN + len(TWEET_SUFFIX)
        if img_path:  # Image counts as a link
            extra_text_len += T_CO_LINKS_LEN
        post_text = strip_title(post, TWEET_MAX_LEN - extra_text_len) + extra_text
        print('[bot] Posting this link on Twitter')
        print(post_text)
        if img_path:
            print('[bot] With image ' + img_path)
            api.update_with_media(filename=img_path, status=post_text)
        else:
            api.update_status(status=post_text)
        log_tweet(post_id)
        time.sleep(DELAY_BETWEEN_TWEETS)


def log_tweet(post_id):
    """Takes note of when the reddit Twitter bot tweeted a post."""
    with open(POSTED_CACHE, 'a') as out_file:
        out_file.write(str(post_id) + '\n')


def main():
    """Runs through the bot posting routine once."""
    # If the tweet tracking file does not already exist, create it
    if not os.path.exists(POSTED_CACHE):
        with open(POSTED_CACHE, 'w'):
            pass
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
    post_dict, post_ids = tweet_creator(subreddit)
    tweeter(post_dict, post_ids)

    # Clean out the image cache
    for filename in glob(IMAGE_DIR + '/*'):
        os.remove(filename)


if __name__ == '__main__':
    main()
