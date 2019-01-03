# -*- coding: utf-8 -*-

import tweepy
from datetime import datetime
import praw
import requests
import os
import urllib.parse
import random

# TODO: Put this all in a config.ini file

# Place your reddit API keys here
CLIENT_ID = ''
CLIENT_SECRET = ''
USER_AGENT = ''

# Place the subreddit you want to look up posts from here
SUBREDDIT_TO_MONITOR = 'elitedangerous'

# Place the minimum no. of votes for rising posts you want to tweet
POST_SCORE_THRESHOLD = 30

# Place your twitter API keys here
ACCESS_TOKEN = ''
ACCESS_TOKEN_SECRET = ''
CONSUMER_KEY = ''
CONSUMER_SECRET = ''

# Place the name of the folder where the images are downloaded
IMAGE_DIR = ''

# Place the hashtags you want to include with each tweet
HASHTAGS = '#EliteDangerous #EliteReddit'

# Place the maximum length for a tweet
TWEET_MAX_LEN = 280

# Place the lengths of t.co links (cf https://dev.twitter.com/overview/t.co)
T_CO_LINKS_LEN = 24

# Probability to try and get a rising post with each func call
PROBABILITY = '30%'

NSFW_ALLOWED = False

SPOILERS_ALLOWED = False

EXCLUDED_FLAIRS = 'help, modpost, meta'.split(', ')

EXCLUDED_KEYWORDS = 'hate, braben, shit, rank, pad, pvp'.split(', ')

# Min number of hours since last tweet
MIN_TIME_SINCE_LAST = 5

# Probability that a post will be tweeted if the time since last exceeds the previously specified min no. of hours
TWEET_PROBABILITY = '70%'


def setup_connection_reddit(subreddit):
    """Creates a read-only connection to the reddit API."""

    print('[bot] Setting up connection with reddit')
    reddit_api = praw.Reddit(client_id=CLIENT_ID,
                             client_secret=CLIENT_SECRET,
                             user_agent=USER_AGENT)

    return reddit_api.subreddit(subreddit)


def strip_title(title, num_characters):
    """ Shortens the title of the post to the 28- character limit. """
    if len(title) <= num_characters:
        return title
    else:
        return title[:num_characters - 1] + '…'


def already_tweeted(post_id):
    """ Checks if the reddit Twitter bot has already tweeted a post. """
    found = False
    with open('cache.txt', 'r') as in_file:
        for line in in_file.read().split(', '):
            if line == post_id:
                found = True
                break
    in_file.close()
    return found


def passes_criteria(submission):
    """ Takes a submission and checks if it passes all the criteria specified in the config """

    # Ugly as hell, refine code later
    if (NSFW_ALLOWED is False) and submission.over_18:
        return False
    if (SPOILERS_ALLOWED is False) and submission.spoiler:
        return False
    if any(keyword in submission.title.lower() for keyword in EXCLUDED_KEYWORDS):
        return False
    if any(flair == str(submission.link_flair_text).replace('None', '').lower() for flair in EXCLUDED_FLAIRS):
        return False
    if submission.score < POST_SCORE_THRESHOLD:
        return False
    return True


def grabber_func(subreddit_info):
    """ Gets a post from the subreddit for tweeting. """

    print('[bot] Getting posts from reddit\n')
    # roll a dice, if it lands on 6, search for a good rising post
    if random.random() <= (float(PROBABILITY.replace('%', ''))/100):
        print('[bot] Attempting to find a good rising post')
        for submission in subreddit_info.rising():
            if passes_criteria(submission):
                print('[bot] Found a good rising post')
                return submission
        else:
            print('[bot] Failed to find a good rising post')

    # Cycles through hot posts
    for submission in subreddit_info.hot(limit=15):
        # only insert records that aren't already tweeted
        if not already_tweeted(submission.id):
            if submission.stickied is False and passes_criteria(submission):
                return submission
            else:
                print('[bot] Not tweeting {}: Failed criteria.\n'.format(str(submission.id)))
        else:
            print('[bot] Already stored: {}\n'.format(str(submission.id)))
    return None


def tweeter_func(twitter_api, submission):
    """ Takes a PRAW submission object and tweets it"""

    img_path = get_media(submission.url)

    extra_text = ' by ' + str(submission.author.name).replace('None', '[deleted]') \
                 + '\n' + HASHTAGS + '\n' + 'https://redd.it/'+submission.id
    extra_text_len = len(extra_text)
    if img_path:  # Image counts as a link
        extra_text_len += T_CO_LINKS_LEN  # not fully accurate, work on later
    post_text = '"' + strip_title(submission.title, TWEET_MAX_LEN - extra_text_len - 2) + '"' + extra_text
    print('[bot] Posting this link on Twitter')
    print(post_text + '\n')
    if img_path:
        print('[bot] With image ' + img_path)
        twitter_api.update_with_media(filename=img_path, status=post_text)
        os.remove(img_path)  # remove image from disk once tweeted
        print('[bot] Deleted image')
    else:
        twitter_api.update_status(status=post_text)

    print('[bot] Marking post as tweeted')
    with open('cache.txt', 'a+') as file:
        file.write(submission.id+', ')
    file.close()


def get_media(img_url):
    """Downloads i.imgur.com and i.redd.it images that reddit posts may point to."""

    # convert single-image non-gallery imgur links into direct jpg links
    if 'imgur.com' in img_url and not any(x in img_url for x in ('gallery', '/a/', 'i.')):
        img_url = 'https://i.imgur.com/{}.jpg'.format(os.path.basename(urllib.parse.urlsplit(img_url).path))

    if ('i.imgur.com' in img_url) or ('i.redd.it' in img_url) or ('cdn.discordapp.com' in img_url):
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


def main():
    """ Checks the time since last tweet, and decides to tweet semi-randomly. """

    print('[bot] Waking up\n')
    # create directories, database, table and trigger upon initial startup
    if not os.path.exists(IMAGE_DIR):
        print('[bot] Making image directory')
        os.makedirs(IMAGE_DIR)
    if not os.path.exists('cache.txt'):
        with open('cache.txt', 'w+') as file:
            pass
        file.close()

    auth = tweepy.OAuthHandler(CONSUMER_KEY, CONSUMER_SECRET)
    auth.set_access_token(ACCESS_TOKEN, ACCESS_TOKEN_SECRET)
    twitter_api = tweepy.API(auth)
    print('[bot] Successfully auth\'d with twitter, getting user_timeline')

    last_status = twitter_api.user_timeline(count=1)[0]
    since_last = (datetime.utcnow() - last_status.created_at)
    # tweet every X hours + some randomness
    if since_last.total_seconds() > MIN_TIME_SINCE_LAST*60*60 \
            and random.random() < float(TWEET_PROBABILITY.replace('%', ''))/100:
        print('[bot] Conditional passed, igniting engines')
        subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
        post = grabber_func(subreddit)
        if post is not None:
            tweeter_func(twitter_api, post)

    else:
        print('[bot] Conditional failed, going back to sleep')


if __name__ == '__main__':
    main()
