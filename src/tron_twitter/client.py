"""Twikit wrapper — stateless operations authed via environment cookies."""

import asyncio

from twikit import Client

from .config import load_cookies, load_state


def get_client() -> Client:
    return Client("en-US")


async def authed_client() -> Client:
    """Build a `Client` and apply cookies from `TRON_TWITTER_COOKIES`."""
    cookies = load_cookies()
    client = get_client()
    client.set_cookies(
        {"auth_token": cookies["auth_token"], "ct0": cookies["ct0"]},
        clear_cookies=True,
    )
    return client


async def check_session() -> dict:
    """Validate the current session."""
    try:
        client = await authed_client()
    except Exception as e:
        return {"valid": False, "reason": str(e)}
    try:
        user = await client.user()
        return {"valid": True, "user": format_user(user)}
    except Exception as e:
        return {"valid": False, "reason": str(e)}


# --- Read operations ---


async def search_tweets(query: str, count: int = 20, product: str = "Top") -> list[dict]:
    client = await authed_client()
    result = await client.search_tweet(query, product=product, count=count)
    return [format_tweet(t) for t in result]


async def get_trending(category: str = "trending", count: int = 20) -> list[dict]:
    client = await authed_client()
    trends = await client.get_trends(category, count=count)
    return [format_trend(t) for t in trends]


async def get_timeline(username: str, count: int = 20) -> list[dict]:
    client = await authed_client()
    user = await client.get_user_by_screen_name(username)
    result = await client.get_user_tweets(user.id, "Tweets", count=count)
    return [format_tweet(t) for t in result]


async def get_user(username: str) -> dict:
    client = await authed_client()
    user = await client.get_user_by_screen_name(username)
    return format_user(user)


async def get_tweet(tweet_id: str) -> dict:
    client = await authed_client()
    tweet = await client.get_tweet_by_id(tweet_id)
    return format_tweet(tweet)


async def get_notifications(type: str = "All", count: int = 20) -> list[dict]:
    client = await authed_client()
    result = await client.get_notifications(type, count=count)
    return [format_notification(n) for n in result]


async def check_mentions(peek: bool = False) -> dict:
    """Get new mentions since the bookmark in `TRON_TWITTER_STATE`.

    Returns an envelope:
        {"items": [...], "state": {...}}

    `state` is the bookmark to persist back to the caller's state store
    (e.g. the Tron vault). With `peek=True`, `state` is unchanged.
    """
    state = load_state()
    last_ts = int(state.get("last_mention_ts", 0) or 0)

    notifications = await get_notifications("Mentions")
    new_mentions = [
        n for n in notifications
        if int(n.get("timestamp_ms", 0)) > last_ts
    ]

    new_state = dict(state)
    if new_mentions and not peek:
        new_state["last_mention_ts"] = max(int(n["timestamp_ms"]) for n in new_mentions)

    return {"items": new_mentions, "state": new_state}


DM_INBOX_PARAMS = {
    "context": "FETCH_DM_CONVERSATION",
    "include_profile_interstitial_type": "1",
    "include_blocking": "1",
    "include_blocked_by": "1",
    "include_followed_by": "1",
    "include_want_retweets": "1",
    "include_mute_edge": "1",
    "include_can_dm": "1",
    "include_can_media_tag": "1",
    "include_ext_is_blue_verified": "1",
    "include_ext_verified_type": "1",
    "include_ext_profile_image_shape": "1",
    "skip_status": "1",
    "dm_secret_conversations_enabled": "false",
    "krs_registration_enabled": "true",
    "cards_platform": "Web-12",
    "include_cards": "1",
    "include_ext_alt_text": "true",
    "include_ext_limited_action_results": "false",
    "include_quote_count": "true",
    "include_reply_count": "1",
    "tweet_mode": "extended",
    "include_ext_views": "true",
    "dm_users": "false",
    "include_groups": "true",
    "include_inbox_timelines": "true",
    "include_ext_media_color": "true",
    "supports_reactions": "true",
    "include_conversation_info": "true",
}

DM_INBOX_URL = "https://x.com/i/api/1.1/dm/inbox_initial_state.json"


async def get_dm_inbox() -> dict:
    """Fetch the DM inbox via Twitter's internal API."""
    client = await authed_client()
    response, _ = await client.get(
        DM_INBOX_URL,
        params=DM_INBOX_PARAMS,
        headers=client._base_headers,
    )
    inbox = response.get("inbox_initial_state", response)
    users = inbox.get("users", {})

    conversations = []
    for conv_id, conv in inbox.get("conversations", {}).items():
        conv_data = {
            "conversation_id": conv_id,
            "type": conv.get("type"),
            "sort_timestamp": conv.get("sort_timestamp"),
            "participants": [],
        }
        for p in conv.get("participants", []):
            uid = p.get("user_id", "")
            user_info = users.get(uid, {})
            conv_data["participants"].append({
                "user_id": uid,
                "name": user_info.get("name", ""),
                "screen_name": user_info.get("screen_name", ""),
            })
        for entry in inbox.get("entries", []):
            msg = entry.get("message", {})
            if msg.get("conversation_id") == conv_id:
                md = msg.get("message_data", {})
                conv_data["last_message"] = {
                    "id": md.get("id"),
                    "time": md.get("time"),
                    "text": md.get("text", ""),
                    "sender_id": md.get("sender_id"),
                }
                break
        conversations.append(conv_data)

    conversations.sort(key=lambda c: c.get("sort_timestamp", "0"), reverse=True)
    return {"conversations": conversations, "total": len(conversations)}


async def get_dm_history(user_id: str, count: int = 20) -> list[dict]:
    client = await authed_client()
    result = await client.get_dm_history(user_id)
    messages = list(result)[:count]
    return [format_message(m) for m in messages]


async def get_dm_history_by_username(username: str, count: int = 20) -> list[dict]:
    client = await authed_client()
    user = await client.get_user_by_screen_name(username)
    result = await client.get_dm_history(user.id)
    messages = list(result)[:count]
    return [format_message(m) for m in messages]


async def send_dm(user_id: str, text: str) -> dict:
    client = await authed_client()
    msg = await client.send_dm(user_id, text)
    return format_message(msg)


async def send_dm_by_username(username: str, text: str) -> dict:
    client = await authed_client()
    user = await client.get_user_by_screen_name(username)
    msg = await client.send_dm(user.id, text)
    return format_message(msg)


async def check_dms(peek: bool = False) -> dict:
    """Get new DMs since the bookmark in `TRON_TWITTER_STATE`.

    Returns an envelope:
        {"items": [...], "state": {...}}

    `state` is the bookmark to persist back to the caller's state store.
    With `peek=True`, `state` is unchanged.
    """
    client = await authed_client()
    state = load_state()
    last_ts = state.get("last_dm_ts", "0") or "0"

    me = await client.user()
    my_id = me.id

    response, _ = await client.get(
        DM_INBOX_URL,
        params=DM_INBOX_PARAMS,
        headers=client._base_headers,
    )
    inbox = response.get("inbox_initial_state", response)
    users = inbox.get("users", {})

    new_messages = []
    for entry in inbox.get("entries", []):
        msg = entry.get("message")
        if not msg:
            continue
        md = msg.get("message_data", {})
        sender_id = md.get("sender_id", "")
        msg_time = md.get("time", "0")

        if sender_id == my_id:
            continue
        if msg_time <= last_ts:
            continue

        sender_info = users.get(sender_id, {})
        new_messages.append({
            "id": md.get("id"),
            "time": msg_time,
            "text": md.get("text", ""),
            "sender_id": sender_id,
            "sender_screen_name": sender_info.get("screen_name", ""),
            "sender_name": sender_info.get("name", ""),
            "conversation_id": msg.get("conversation_id"),
            "attachment": md.get("attachment"),
        })

    new_messages.sort(key=lambda m: m["time"])

    new_state = dict(state)
    if new_messages and not peek:
        new_state["last_dm_ts"] = max(m["time"] for m in new_messages)

    return {"items": new_messages, "state": new_state}


# --- Write operations ---


async def post_tweet(text: str) -> dict:
    client = await authed_client()
    tweet = await client.create_tweet(text=text)
    return format_tweet(tweet)


async def reply_to_tweet(tweet_id: str, text: str) -> dict:
    client = await authed_client()
    tweet = await client.create_tweet(text=text, reply_to=tweet_id)
    return format_tweet(tweet)


async def like_tweet(tweet_id: str) -> dict:
    client = await authed_client()
    await client.favorite_tweet(tweet_id)
    return {"liked": True, "tweet_id": tweet_id}


async def retweet_tweet(tweet_id: str) -> dict:
    client = await authed_client()
    await client.retweet(tweet_id)
    return {"retweeted": True, "tweet_id": tweet_id}


async def follow_user_by_username(username: str) -> dict:
    client = await authed_client()
    user = await client.get_user_by_screen_name(username)
    await client.follow_user(user.id)
    return {"followed": True, "username": username, "user_id": user.id}


async def unfollow_user_by_username(username: str) -> dict:
    client = await authed_client()
    user = await client.get_user_by_screen_name(username)
    await client.unfollow_user(user.id)
    return {"unfollowed": True, "username": username, "user_id": user.id}


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


def format_message(msg) -> dict:
    return {
        "id": msg.id,
        "time": msg.time,
        "text": msg.text,
        "sender_id": msg.sender_id,
        "recipient_id": msg.recipient_id,
        "attachment": msg.attachment,
    }


def format_notification(notif) -> dict:
    data = {
        "id": notif.id,
        "timestamp_ms": notif.timestamp_ms,
        "message": notif.message,
        "icon": notif.icon,
    }
    if notif.tweet:
        data["tweet"] = format_tweet(notif.tweet)
    if notif.from_user:
        data["from_user"] = {
            "name": notif.from_user.name,
            "screen_name": notif.from_user.screen_name,
        }
    return data


def format_trend(trend) -> dict:
    return {
        "name": trend.name,
        "tweets_count": trend.tweets_count,
        "domain_context": trend.domain_context,
    }


def run_async(coro):
    """Run an async coroutine from sync context."""
    return asyncio.run(coro)
