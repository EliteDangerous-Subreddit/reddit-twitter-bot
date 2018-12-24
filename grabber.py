# -*- coding: utf-8 -*-

"""
Copyright 2015 Randal S. Olson and 2018 Deadstar106? All I'm doing is mangling it worse

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
import requests
import os
import urllib.parse
import random
import sqlite3

# Place your reddit API keys here
CLIENT_ID = ''
CLIENT_SECRET = ''
USER_AGENT = ''

# Place the subreddit you want to look up posts from here
SUBREDDIT_TO_MONITOR = 'elitedangerous'

# Place the minimum no. of votes for rising posts you want to tweet
POST_SCORE_THRESHOLD = 30

# Place the name of the folder where the images are downloaded
IMAGE_DIR = ''


def setup_connection_reddit(subreddit):
    """Creates a read-only connection to the reddit API."""

    print('[bot] Setting up connection with reddit')
    reddit_api = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent=USER_AGENT)

    return reddit_api.subreddit(subreddit)


def get_image(img_url):
    """Downloads i.imgur.com and i.redd.it images that reddit posts may point to."""

    # convert single-image non-gallery imgur links into direct jpg links
    if 'imgur.com' in img_url and not any(x in img_url for x in ('gallery', '/a/', 'i.')):
        img_url = 'https://i.imgur.com/{}.jpg'.format(os.path.basename(urllib.parse.urlsplit(img_url).path))

    if ('i.imgur.com' in img_url) or ('i.redd.it' in img_url):
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


def grabber_func(subreddit_info, cursor):
    """Looks up posts 3 posts from reddit and stores them in SQLite"""

    print('[bot] Getting posts from reddit\n')

    # Cycles through hot posts + some rising ones until it stores 3 posts total
    counter = 0
    hot_gen = subreddit_info.hot()
    while counter < 3:

        if random.randrange(6) == 5:
            print('[bot] Attempting to find a good rising post')
            for post in subreddit_info.rising():
                if post.score > POST_SCORE_THRESHOLD:
                    print('[bot] Found a good rising post')
                    submission = post
                    break
            else:
                print('[bot] Failed to find a good rising post')
                submission = hot_gen.next()

        else:
            submission = hot_gen.next()

        # only insert records that aren't already in the db
        t = (submission.id,)
        cursor.execute('SELECT count(*) FROM tblqueue WHERE id=?', t)
        if int(cursor.fetchone()[0]) < 1:
            if submission.stickied is False:

                contents = (submission.id, submission.title, '/u/'+submission.author.name,
                            submission.created_utc, get_image(submission.url), 0)

                print('[bot] Inserting {} into database\n'.format(str(submission.id)))
                cursor.execute('INSERT INTO tblqueue VALUES (?, ?, ?, ?, ?, ?)', contents)
                counter += 1
                if counter == 3:
                    break
            else:
                print('[bot] Not tweeting {}: stickied post.\n'.format(str(submission.id)))

        else:
            print('[bot] Already stored: {}\n'.format(str(submission.id)))


def fancy_remove(post_id, img_path):
    """ Helper function that deletes images from removed records and tells the user about it """

    if img_path is not '':
        print('[bot] Removing image {} taken from post kicked out of db'.format(img_path))
        os.remove(img_path)
    print('[bot] Removing post {} from db due to size limit on untweeted items\n'.format(post_id))


def main():
    """ Runs through the program once, grabs 3 posts from Reddit and stores them in SQLite """
    print('[bot] Initiating launch sequence')

    # create directories, database, table and trigger upon initial startup
    if not os.path.exists(IMAGE_DIR):
        print('[bot] Making image directory')
        os.makedirs(IMAGE_DIR)

    db = sqlite3.connect('posts.db')  # connect to the db and create it if it doesn't exist already
    c = db.cursor()

    # is_tweeted is a self-explanatory boolean value, in SQLite 0 = False and 1 = True
    c.execute('''CREATE TABLE IF NOT EXISTS tblqueue
                 (id TEXT PRIMARY KEY, title TEXT, user TEXT, 
                 created_at BIGINT, image_path TEXT, is_tweeted INT)''')

    # The trigger enforces the size limit on the db (5 untweeted records max)
    # Previously-tweeted records remain in the db in order to check future posts
    # The trigger also calls functions that remove the images of deleted records and tells the user about it.

    db.create_function('del_item', 2, fancy_remove)

    c.execute('''    
    CREATE TRIGGER IF NOT EXISTS limit_size
    AFTER INSERT ON tblqueue
    BEGIN
        SELECT del_item(id, image_path) FROM tblqueue 
        WHERE created_at = (SELECT min(created_at) FROM tblqueue WHERE is_tweeted = 0)
        AND (SELECT count(*) FROM tblqueue WHERE is_tweeted = 0) = 6;
        
        DELETE FROM tblqueue WHERE 
        created_at = (SELECT min(created_at) FROM tblqueue WHERE is_tweeted = 0) 
        AND (SELECT count(*) FROM tblqueue WHERE is_tweeted = 0) = 6; 
    END
    ;
    ''')

    subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
    grabber_func(subreddit, c)
    # for row in c.execute('SELECT * FROM tblqueue').fetchall():
    #    print(row)
    db.commit()  # commit changes to the db
    db.close()
    print('[bot] Closed')


if __name__ == '__main__':
    main()
