# -*- coding: utf-8 -*-

import tweepy
from datetime import datetime
import praw
import requests
import os
import urllib.parse
import random
import configparser


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

    conditionals = [
        (NSFW_ALLOWED is False) and submission.over_18,
        (SPOILERS_ALLOWED is False) and submission.spoiler,
        any([keyword in submission.title.lower() for keyword in EXCLUDED_KEYWORDS]),
        any([flair == str(submission.link_flair_text).replace('None', '').lower() for flair in EXCLUDED_FLAIRS]),
        submission.score < POST_SCORE_THRESHOLD,
        already_tweeted(submission.id) is True
    ]

    if any(conditionals):
        return False
    return True


def grabber_func(subreddit_info):
    """ Gets a post from the subreddit for tweeting. """

    print('[bot] Getting posts from reddit\n')
    # The probability of checking 'rising' is set by the user
    if random.random() <= (float(RISING_PROBABILITY)/100):
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
        if submission.stickied is False and passes_criteria(submission):
            return submission
          else:
            print('[bot] Not tweeting {}: Failed criteria.\n'.format(str(submission.id)))
    
    return None


def tweeter_func(twitter_api, submission):
    """ Takes a PRAW submission object and tweets it """

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
            
            if os.path.getsize(img_path) >= (3072 * 1024):
                print('[bot] File size too big for twitter. Deleting image and continuing')
                os.remove(img_path)
                return ''
            
            return img_path
        else:
            print('[bot] Image failed to download. Status code: ' + resp.status_code)
    else:
        print('[bot] Post doesn\'t point to an i.imgur.com or i.redd.it link')
    return ''


def main():
    """ Checks the time since last tweet, and decides to tweet semi-randomly. """

    print('[bot] Waking up\n')
    # create directories upon initial startup
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
    print("[bot] Successfully auth'd with twitter, getting user_timeline")

    last_status = twitter_api.user_timeline(count=1)[0]
    since_last = (datetime.utcnow() - last_status.created_at)
    # tweet every X hours + some randomness
    if since_last.total_seconds() > MIN_TIME_SINCE_LAST*60*60 \
            and random.random() < float(TWEET_PROBABILITY)/100:
        print('[bot] Conditional passed, igniting engines')
        subreddit = setup_connection_reddit(SUBREDDIT_TO_MONITOR)
        post = grabber_func(subreddit)
        if post is not None:
            tweeter_func(twitter_api, post)
        else:
            print('[bot] Failed to find a good post, going back to sleep')

    else:
        print('[bot] Conditional failed, going back to sleep')


# Initialize global variables from config file
config = configparser.ConfigParser()
config.read('config.ini')

reddit = config['reddit.com']
CLIENT_ID            = reddit.get('client_id')
CLIENT_SECRET        = reddit.get('client_secret')
USER_AGENT           = reddit.get('user_agent')

twitter = config['twitter.com']
ACCESS_TOKEN         = twitter.get('access_token')
ACCESS_TOKEN_SECRET  = twitter.get('access_token_secret')
CONSUMER_KEY         = twitter.get('consumer_key')
CONSUMER_SECRET      = twitter.get('consumer_secret')
TWEET_MAX_LEN        = int(twitter.get('tweet_max_len'))
T_CO_LINKS_LEN       = int(twitter.get('t_co_links_len'))

settings = config['twitter-bot-settings']
SUBREDDIT_TO_MONITOR = settings.get('subreddit_to_monitor')
POST_SCORE_THRESHOLD = int(settings.get('post_score_threshold'))
IMAGE_DIR            = settings.get('image_dir')
RISING_PROBABILITY   = float(settings.get('rising_probability'))
NSFW_ALLOWED         = bool(settings.get('nsfw_allowed'))
SPOILERS_ALLOWED     = bool(settings.get('spoilers_allowed'))
MIN_TIME_SINCE_LAST  = int(settings.get('min_time_since_last'))
TWEET_PROBABILITY    = float(settings.get('tweet_probability'))
EXCLUDED_FLAIRS      = settings.get('excluded_flairs').split(', ')
EXCLUDED_KEYWORDS    = settings.get('excluded_keywords').split(', ')
HASHTAGS             = ' '.join(['#'+hashtag for hashtag in settings.get('hashtags').split(', ')])

if __name__ == '__main__':
    main()
