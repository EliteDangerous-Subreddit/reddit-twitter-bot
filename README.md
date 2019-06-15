# /r/EliteDangerous Reddit Twitter Bot

A Python bot that looks up posts from Reddit and submits them on Twitter.

## Disclaimer

We hold no liability for what you do with this script or what happens to you by using this script. Abusing this script *can* get you banned from Twitter, so make sure to read up on proper usage of the Twitter API.

## Dependencies

You will need to install Python's [tweepy](https://github.com/tweepy/tweepy), [schedule](https://pypi.org/project/schedule/), and [PRAW](https://praw.readthedocs.org/en/) libraries first:

    pip install tweepy
    pip install praw
    pip install schedule

Alternatively, using the requirements file should do it.
1. `pip install -r requirements.txt`
    
You will also need to create an app account on Twitter: [[instructions]](https://dev.twitter.com/apps)

1. Sign in with your Twitter account
2. Create a new app account?
3. Go through the circus hoops to get API access
4. Put all the keys in the provided config file

## Usage

1. Upon downloading the repo, rename config.example.ini to config.ini
2. Go into the freshly-renamed config.ini and enter your reddit API keys and bot-related settings
3. Use task scheduler (Windows) or crontab (linux) to run the python file multiple time per day, recommend hourly. The script will tweet semi-randomly throughout the day at a rate of which you decide.
 
Look further into the config file itself for specific configuration options of the bot.

## Have questions? Need help with the bot?

If you're having issues with or have questions about the bot, please [file an issue](https://github.com/EliteDangerous-Subreddit/reddit-twitter-bot/issues) in this repository so one of the code monkeys can get back to you. Please check the existing (and closed) issues to make sure your issue hasn't already been addressed.
