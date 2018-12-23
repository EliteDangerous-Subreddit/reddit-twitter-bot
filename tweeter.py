# -*- coding: utf-8 -*-

"""
Copyright 2015 Randal S. Olson and 2018 Deadstar106?

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

# Place your Twitter API keys here
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Place the name of the folder where the images are downloaded
IMAGE_DIR = ''

# Place the string you want to add at the end of your tweets (can be empty)
TWEET_SUFFIX = '#EliteDangerous #EliteReddit'

# Place the maximum length for a tweet
TWEET_MAX_LEN = 280

# Place the lengths of t.co links (cf https://dev.twitter.com/overview/t.co)
T_CO_LINKS_LEN = 24


def strip_title(title, num_characters):
    """ Shortens the title of the post to the 140 character limit. """
    if len(title) <= num_characters:
        return title
    else:
        return title[:num_characters - 1] + '…'


def tweeter_func(cursor):
    """ Tweets the oldest untweeted post in the db (FIFO) """
    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    api = tweepy.API(auth)

    cursor.execute('''SELECT * FROM tblqueue 
                      WHERE created_at = (SELECT min(created_at) FROM tblqueue WHERE is_tweeted = 0)''')

    post = cursor.fetchone()
    img_path = post[4]

    extra_text = ' by ' + post[2] + '\n' + TWEET_SUFFIX + '\n' + 'https://redd.it/'+post[0]
    extra_text_len = 2 + 4 + len(post[2]) + 1 + len(TWEET_SUFFIX) + 1 + len('https://redd.it/'+post[0])
    if img_path:  # Image counts as a link
        extra_text_len += T_CO_LINKS_LEN  # not fully accurate, work on later
    post_text = '"' + strip_title(post[1], TWEET_MAX_LEN - extra_text_len) + '"' + extra_text
    print('[bot] Posting this link on Twitter')
    print(post_text + '\n')
    if img_path:
        print('[bot] With image ' + img_path)
        api.update_with_media(filename=img_path, status=post_text)
        os.remove(img_path)  # remove image from disk once tweeted
    else:
        api.update_status(status=post_text)

    print('[bot] Marking post as tweeted')
    cursor.execute('''UPDATE tblqueue SET is_tweeted = 1
                   WHERE created_at = (SELECT min(created_at) FROM tblqueue WHERE is_tweeted = 0)''')


def main():
    """ Runs through the bot posting routine once, tweeting oldest items in queue. """

    print('[bot] Igniting engines')
    if not os.path.exists(IMAGE_DIR):
        print('[bot] Making image directory')
        os.makedirs(IMAGE_DIR)

    db = sqlite3.connect('posts.db')
    c = db.cursor()

    # is_tweeted is a self-explanatory boolean value, in SQLite 0 = False and 1 = True
    c.execute('''CREATE TABLE IF NOT EXISTS tblqueue
                 (id TEXT PRIMARY KEY, title TEXT, post_link TEXT, 
                 created_at BIGINT, image_path TEXT, is_tweeted INT)''')

    tweeter_func(c)
    # for row in c.execute('SELECT * FROM tblqueue').fetchall():
    #    print(row)
    db.commit()
    db.close()


if __name__ == '__main__':
    main()
