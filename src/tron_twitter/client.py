"""Twikit wrapper — auth, session management, and formatted output."""

import asyncio
import json
from datetime import datetime, timezone

from twikit import Client

from .config import COOKIES_PATH, ensure_dirs


def get_client() -> Client:
    return Client("en-US")


async def load_session(client: Client) -> bool:
    """Load saved cookies. Returns True if cookies exist."""
    if not COOKIES_PATH.exists():
        return False
    client.load_cookies(str(COOKIES_PATH))
    return True


async def save_session(client: Client):
    """Save current cookies to disk."""
    ensure_dirs()
    client.save_cookies(str(COOKIES_PATH))


async def login_with_credentials(username: str, email: str, password: str) -> Client:
    client = get_client()
    await client.login(
        auth_info_1=username,
        auth_info_2=email,
        password=password,
    )
    await save_session(client)
    return client


async def login_with_cookies(auth_token: str, ct0: str) -> Client:
    client = get_client()
    client.set_cookies({"auth_token": auth_token, "ct0": ct0}, clear_cookies=True)
    await save_session(client)
    return client


async def check_session() -> dict:
    """Validate the current session. Returns status info."""
    client = get_client()
    if not await load_session(client):
        return {"valid": False, "reason": "No saved cookies"}
    try:
        # Attempt a lightweight call to validate the session
        user = await client.user()
        return {
            "valid": True,
            "user": format_user(user),
        }
    except Exception as e:
        return {"valid": False, "reason": str(e)}


# --- Read operations ---


async def search_tweets(query: str, count: int = 20, product: str = "Top") -> list[dict]:
    client = get_client()
    await load_session(client)
    result = await client.search_tweet(query, product=product, count=count)
    return [format_tweet(t) for t in result]


async def get_trending(category: str = "trending", count: int = 20) -> list[dict]:
    client = get_client()
    await load_session(client)
    trends = await client.get_trends(category, count=count)
    return [format_trend(t) for t in trends]


async def get_timeline(username: str, count: int = 20) -> list[dict]:
    client = get_client()
    await load_session(client)
    user = await client.get_user_by_screen_name(username)
    result = await client.get_user_tweets(user.id, "Tweets", count=count)
    return [format_tweet(t) for t in result]


async def get_user(username: str) -> dict:
    client = get_client()
    await load_session(client)
    user = await client.get_user_by_screen_name(username)
    return format_user(user)


async def get_tweet(tweet_id: str) -> dict:
    client = get_client()
    await load_session(client)
    tweet = await client.get_tweet_by_id(tweet_id)
    return format_tweet(tweet)


# --- Write operations ---


async def post_tweet(text: str) -> dict:
    client = get_client()
    await load_session(client)
    tweet = await client.create_tweet(text=text)
    return format_tweet(tweet)


async def reply_to_tweet(tweet_id: str, text: str) -> dict:
    client = get_client()
    await load_session(client)
    tweet = await client.create_tweet(text=text, reply_to=tweet_id)
    return format_tweet(tweet)


async def like_tweet(tweet_id: str) -> dict:
    client = get_client()
    await load_session(client)
    await client.favorite_tweet(tweet_id)
    return {"liked": True, "tweet_id": tweet_id}


async def retweet_tweet(tweet_id: str) -> dict:
    client = get_client()
    await load_session(client)
    await client.retweet(tweet_id)
    return {"retweeted": True, "tweet_id": tweet_id}


# --- Formatters ---


def format_tweet(tweet) -> dict:
    return {
        "id": tweet.id,
        "text": tweet.full_text or tweet.text,
        "created_at": tweet.created_at,
        "user": {
            "name": tweet.user.name,
            "screen_name": tweet.user.screen_name,
            "verified": tweet.user.is_blue_verified,
        },
        "metrics": {
            "replies": tweet.reply_count,
            "retweets": tweet.retweet_count,
            "likes": tweet.favorite_count,
            "quotes": tweet.quote_count,
            "views": tweet.view_count,
        },
        "url": f"https://x.com/{tweet.user.screen_name}/status/{tweet.id}",
    }


def format_user(user) -> dict:
    return {
        "id": user.id,
        "name": user.name,
        "screen_name": user.screen_name,
        "description": user.description,
        "location": user.location,
        "url": user.url,
        "verified": user.is_blue_verified,
        "followers": user.followers_count,
        "following": user.following_count,
        "tweets": user.statuses_count,
        "created_at": user.created_at,
        "profile_url": f"https://x.com/{user.screen_name}",
    }


def format_trend(trend) -> dict:
    return {
        "name": trend.name,
        "tweets_count": trend.tweets_count,
        "domain_context": trend.domain_context,
    }


def run_async(coro):
    """Run an async coroutine from sync context."""
    return asyncio.run(coro)
