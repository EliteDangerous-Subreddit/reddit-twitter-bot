#/r/EliteDangerous Reddit Twitter Bot

A Python bot that looks up posts from Reddit, stores them, and later posts them on Twitter.

##Disclaimer

We hold no liability for what you do with this script or what happens to you by using this script. Abusing this script *can* get you banned from Twitter, so make sure to read up on proper usage of the Twitter API.

##Dependencies

You will need to install Python's [tweepy](https://github.com/tweepy/tweepy) and [PRAW](https://praw.readthedocs.org/en/) libraries first:

    pip install tweepy
    pip install praw
    
You will also need to create an app account on Twitter: [[instructions]](https://dev.twitter.com/apps)

1. Sign in with your Twitter account
2. Create a new app account
3. Modify the settings for that app account to allow read & write
4. Generate a new OAuth token with those permissions
5. Manually edit this script and put those tokens in the script

##Usage

Once you edit the bot script to provide the necessary API keys and the subreddit you want to tweet from, you can rig the scripts to be ran automatically:

1. Use task scheduler (Windows) or crontab (linux) to run the grabber once per day
2. Run the tweeter hourly, it'll check the time since the last tweet and make a post semi-randomly (~3 times per day)
 
Look into the script itself for configuration options of the bot.

##Have questions? Need help with the bot?

If you're having issues with or have questions about the bot, please [file an issue](https://github.com/EliteDangerous-Subreddit/reddit-twitter-bot/issues) in this repository so one of the project managers can get back to you. Please check the existing (and closed) issues to make sure your issue hasn't already been addressed.
