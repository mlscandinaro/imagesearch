#!/usr/local/bin/python3

# Image Search Twitter Bot
# Maya Scandinaro

import sys
import numpy as np
import tweepy
import itertools
from serpapi.google_search_results import GoogleSearchResults
from pymongo import MongoClient

if sys.version_info[0] < 3:
    raise Exception("Python 3 or a more recent version is required.")

# variables for accessing twitter API
consumer_key = 'YGFNhshOvrvW4iORxZoUnctgX'
consumer_secret_key = 'EUhx6g9gKWU4fMVjqAHOdKRiKyAlb8tLDGPbyvwUZTWs5YlPif'
access_token = '1300458159891333121-Hq59v4LnbuLqhTt21rXq8nuPldKjtM'
access_token_secret = '6JAJBTroehSmaQyoTwppgozo4ENsek9qTTcfwe264N5Si'

# authenticating to access the twitter API
auth = tweepy.OAuthHandler(consumer_key,consumer_secret_key)
auth.set_access_token(access_token,access_token_secret)
api = tweepy.API(auth)

# mongo info
uri = "mongodb+srv://mlscandinaro:7Grry9bNULoaYcrK@cluster0.fdofm.mongodb.net/twitterbot?ssl=true&ssl_cert_reqs=CERT_NONE&retryWrites=true&w=majority"
client = MongoClient(uri)

blocklist = [
    "pinterest",
    "wikipedia",
    "cartoonnetwork",
    "fandom",
    "amino",
    "redbubble",
    "amazon",
    "reddit",
    "fireden",
    "tumgir",
    "wattpad",
    "aliexpress",
    "dictionary",
    "britannica"
]

whitelist = [
    "twitter",
    "deviantart",
    "artstation",
    "instagram"
]

def main():
    checkMentions()

    # deleteTweets()
    # updateRecentTweetId(0)

def checkMentions():
    recentId = getRecentTweetId()
    mentions = api.mentions_timeline(recentId)
    currMaxId = -1;
    
    for mention in mentions:
        currMaxId = max(currMaxId, mention.id)
        try:
            ref = api.get_status(mention.in_reply_to_status_id)
        except:
            api.update_status("Hi @" + mention.user.screen_name + "! Try mentioning me in a reply to a tweet containing an image!", mention.id_str)
        else: 
            if ref.entities['media'][0]['type'] == 'photo':
                result = reverseImgSearch(ref.entities['media'][0]['media_url_https'])
                postTweet(result, mention.user.screen_name, mention.id_str)
            else:
                api.update_status("Hi @" + mention.user.screen_name + "! I can't find an image :( Mention me under a reply to a tweet containing an image.", mention.id_str)
            
    if (currMaxId > recentId):
        updateRecentTweetId(currMaxId)
        print("new recent tweet id: " + str(currMaxId))

def getRecentTweetId():
    db = client.twitterbot
    collection = db.recentid
    entry = collection.find_one({"id":1})
    return entry["tweetid"]

def updateRecentTweetId(id):
    db = client.twitterbot
    collection = db.recentid
    collection.update_one(
        {"id":1}, 
        { "$set": {"tweetid":id}})

def reverseImgSearch(img):
    imgInfo = search(img)
    filteredInfo = filterResults(imgInfo)
    return filteredInfo

def search(img):
    print("\nsearching . . . " + img)
    params = {
      "api_key": "702966ecc0d5ebd35f41bc961ee15cdf419df7b5cd5c25bd2e098ff0cac17d18",
      "engine": "google_reverse_image",
      "google_domain": "google.com",
      "image_url": img,
    }
    client = GoogleSearchResults(params)
    return client.get_dict()

def filterResults(results):
    filtered = []

    # remove links with blocked sites, prioritize whitelisted sites
    for result in results['image_results']:
        if (not inBlocklist(result['link'])):
            if (inWhitelist(result['link'])):
                filtered.insert(0, result)
            else:
                filtered.insert(len(filtered), result)

    # remove duplicate links
    for i in range(len(filtered) - 1):
        for j in range(i + 1, len(filtered)):
            if filtered[i]['displayed_link'] == filtered[j]['displayed_link']:
                filtered.pop(j)
                break

    return filtered

def inBlocklist(result):
    for site in blocklist:
        if site in result:
            return True
    return False

def inWhitelist(result):
    for site in whitelist:
        if site in result:
            return True
    return False

def postTweet(result, user, idStr):
    tweet = ""
    for source in result:
        tweet += source['link'] + "\n"

    print("\nsources found: ")
    if len(result) == 0:
        api.update_status("Hi @" + user + "! Sadly, I couldn't find any related sources!\n" + tweet, idStr) 
        print("no results")
    else:
        api.update_status("Hi @" + user + "! Here are possible sources for this image!\n" + tweet, idStr) 
        print(tweet)

def deleteTweets():
    for status in tweepy.Cursor(api.user_timeline).items():
        api.destroy_status(status.id)
    print("deleted all tweets")

if __name__ == "__main__":
    main()



