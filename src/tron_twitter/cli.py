"""Click CLI for tron-twitter."""

import json
import sys

import click

from . import __version__
from .client import (
    check_mentions,
    check_session,
    get_notifications,
    get_timeline,
    get_trending,
    get_tweet,
    get_user,
    like_tweet,
    login_with_cookies,
    login_with_credentials,
    post_tweet,
    reply_to_tweet,
    retweet_tweet,
    run_async,
    search_tweets,
)


def output(data, fmt: str):
    """Output data in the requested format."""
    if fmt == "json":
        click.echo(json.dumps(data, indent=2, ensure_ascii=False))
    else:
        _print_text(data)


def _print_text(data):
    """Human-readable text output."""
    if isinstance(data, list):
        for i, item in enumerate(data):
            if i > 0:
                click.echo("---")
            _print_item(item)
    else:
        _print_item(data)


def _print_item(item: dict):
    if "text" in item and "user" in item:
        # Tweet
        u = item["user"]
        click.echo(f"@{u['screen_name']} ({u['name']})")
        click.echo(item["text"])
        m = item.get("metrics", {})
        click.echo(
            f"  {m.get('likes', 0)} likes · {m.get('retweets', 0)} RTs · {m.get('replies', 0)} replies"
        )
        click.echo(f"  {item.get('created_at', '')}  {item.get('url', '')}")
    elif "screen_name" in item and "followers" in item:
        # User
        click.echo(f"@{item['screen_name']} ({item['name']})")
        click.echo(item.get("description", ""))
        click.echo(
            f"  {item['followers']} followers · {item['following']} following · {item['tweets']} tweets"
        )
        if item.get("location"):
            click.echo(f"  Location: {item['location']}")
        click.echo(f"  {item.get('profile_url', '')}")
    elif "timestamp_ms" in item and "message" in item:
        # Notification
        click.echo(item.get("message", ""))
        if item.get("from_user"):
            u = item["from_user"]
            click.echo(f"  from @{u['screen_name']} ({u['name']})")
        if item.get("tweet"):
            click.echo(f"  tweet: {item['tweet']['text'][:120]}")
        click.echo(f"  {item.get('timestamp_ms', '')}")
    elif "name" in item and "tweets_count" in item:
        # Trend
        count = item.get("tweets_count")
        count_str = f" ({count:,} tweets)" if count else ""
        ctx = item.get("domain_context") or ""
        click.echo(f"{item['name']}{count_str}  {ctx}")
    else:
        for k, v in item.items():
            click.echo(f"  {k}: {v}")


@click.group()
@click.version_option(__version__)
@click.option("--format", "fmt", type=click.Choice(["json", "text"]), default="json", help="Output format")
@click.pass_context
def main(ctx, fmt):
    """Twitter/X CLI for Tron."""
    ctx.ensure_object(dict)
    ctx.obj["fmt"] = fmt


# --- Auth ---


@main.group()
def auth():
    """Authentication commands."""
    pass


@auth.command("login")
def auth_login():
    """Login with username/email/password."""
    username = click.prompt("Username")
    email = click.prompt("Email")
    password = click.prompt("Password", hide_input=True)
    try:
        run_async(login_with_credentials(username, email, password))
        click.echo("Logged in and cookies saved.")
    except Exception as e:
        click.echo(f"Login failed: {e}", err=True)
        sys.exit(1)


@auth.command("cookies")
def auth_cookies():
    """Login by pasting auth_token and ct0 from browser DevTools."""
    click.echo("Open x.com → DevTools → Application → Cookies")
    auth_token = click.prompt("auth_token")
    ct0 = click.prompt("ct0")
    try:
        run_async(login_with_cookies(auth_token, ct0))
        click.echo("Cookies saved.")
    except Exception as e:
        click.echo(f"Failed: {e}", err=True)
        sys.exit(1)


@auth.command("status")
@click.pass_context
def auth_status(ctx):
    """Check if the current session is valid."""
    result = run_async(check_session())
    output(result, ctx.obj["fmt"])


# --- Read ---


@main.command()
@click.argument("query")
@click.option("--count", default=20, help="Number of results")
@click.option("--product", type=click.Choice(["Top", "Latest", "Media"]), default="Top")
@click.pass_context
def search(ctx, query, count, product):
    """Search tweets."""
    try:
        results = run_async(search_tweets(query, count=count, product=product))
        output(results, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--category", type=click.Choice(["trending", "for-you", "news", "sports", "entertainment"]), default="trending")
@click.option("--count", default=20, help="Number of results")
@click.pass_context
def trending(ctx, category, count):
    """Get trending topics."""
    try:
        results = run_async(get_trending(category=category, count=count))
        output(results, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("username")
@click.option("--count", default=20, help="Number of tweets")
@click.pass_context
def timeline(ctx, username, count):
    """Get a user's recent tweets."""
    try:
        results = run_async(get_timeline(username, count=count))
        output(results, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("username")
@click.pass_context
def user(ctx, username):
    """Get user profile info."""
    try:
        result = run_async(get_user(username))
        output(result, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("tweet_id")
@click.pass_context
def tweet(ctx, tweet_id):
    """Get a single tweet by ID."""
    try:
        result = run_async(get_tweet(tweet_id))
        output(result, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.option("--type", "notif_type", type=click.Choice(["All", "Verified", "Mentions"]), default="All")
@click.option("--count", default=20, help="Number of results")
@click.pass_context
def notifications(ctx, notif_type, count):
    """Get notifications."""
    try:
        results = run_async(get_notifications(notif_type, count=count))
        output(results, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command("check-mentions")
@click.option("--peek", is_flag=True, help="Preview without updating state")
@click.pass_context
def check_mentions_cmd(ctx, peek):
    """Get new mentions since last check (stateful)."""
    try:
        results = run_async(check_mentions(peek=peek))
        output(results, ctx.obj["fmt"])
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# --- Write ---


@main.command()
@click.argument("text")
def post(text):
    """Post a tweet."""
    try:
        result = run_async(post_tweet(text))
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("tweet_id")
@click.argument("text")
def reply(tweet_id, text):
    """Reply to a tweet."""
    try:
        result = run_async(reply_to_tweet(tweet_id, text))
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("tweet_id")
def like(tweet_id):
    """Like a tweet."""
    try:
        result = run_async(like_tweet(tweet_id))
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@main.command()
@click.argument("tweet_id")
def retweet(tweet_id):
    """Retweet a tweet."""
    try:
        result = run_async(retweet_tweet(tweet_id))
        click.echo(json.dumps(result, indent=2, ensure_ascii=False))
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)
