# -*- coding: utf-8 -*-

"""
Copyright 2015 Randal S. Olson and Deadstar106?

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

import tweepy
import os
import sqlite3
from glob import glob

# Place your Twitter API keys here
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Place the name of the folder where the images are downloaded
IMAGE_DIR = 'bin/img'

# Place the name of the file to store the IDs of posts that have been posted
POSTED_CACHE = 'posted_posts.txt'

# Place the string you want to add at the end of your tweets (can be empty)
TWEET_SUFFIX = ' #elitedangerous'

# Place the maximum length for a tweet
TWEET_MAX_LEN = 280

# Place the lengths of t.co links (cf https://dev.twitter.com/overview/t.co)
T_CO_LINKS_LEN = 24


def strip_title(title, num_characters):
    """Shortens the title of the post to the 140 character limit."""
    if len(title) <= num_characters:
        return title
    else:
        return title[:num_characters - 1] + '…'


def log_tweet(post_id):
    """Takes note of when the reddit Twitter bot tweeted a post."""
    with open(POSTED_CACHE, 'a') as out_file:
        out_file.write(str(post_id) + '\n')


def tweeter(cursor):
    """Tweets all of the selected reddit posts."""
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    for 'value' in 'queue':
        img_path = 'img_path'

        extra_text = ' ' + 'link' + TWEET_SUFFIX
        extra_text_len = 1 + T_CO_LINKS_LEN + len(TWEET_SUFFIX)
        if img_path:  # Image counts as a link
            extra_text_len += T_CO_LINKS_LEN
        post_text = strip_title('title', TWEET_MAX_LEN - extra_text_len) + extra_text
        print('[bot] Posting this link on Twitter')
        print(post_text)
        if img_path:
            print('[bot] With image ' + img_path)
            api.update_with_media(filename=img_path, status=post_text)
        else:
            api.update_status(status=post_text)
        log_tweet('post_id')


def main():
    """Runs through the bot posting routine once."""
    #
    if not os.path.exists(IMAGE_DIR):
        os.makedirs(IMAGE_DIR)

    db = sqlite3.connect('posts.db')
    c = db.cursor()
    tweeter(c)
    db.commit()
    db.close()

    # Clean out the image cache
    for filename in glob(IMAGE_DIR + '/*'):
        os.remove(filename)


if __name__ == '__main__':
    main()
