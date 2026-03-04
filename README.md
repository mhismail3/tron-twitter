# tron-twitter

Twitter/X CLI for Tron agent. Wraps [twikit](https://github.com/d60/twikit) for search, trending, timelines, and posting — no API keys required.

## Install

```bash
brew install mhismail3/tools/tron-twitter
```

Or from source:

```bash
pip install .
```

## Auth

Login by pasting cookies from browser DevTools (recommended):

```bash
tron-twitter auth cookies
# Prompts for auth_token and ct0 from x.com → DevTools → Application → Cookies
```

Or via credentials:

```bash
tron-twitter auth login
```

Check session:

```bash
tron-twitter auth status
```

## Usage

```bash
# Search
tron-twitter search "AI agents" --count 10

# Trending
tron-twitter trending --category trending

# User timeline
tron-twitter timeline elonmusk --count 5

# User profile
tron-twitter user elonmusk

# Single tweet
tron-twitter tweet 1234567890

# Post
tron-twitter post "Hello from Tron"

# Reply
tron-twitter reply 1234567890 "Great tweet!"

# Like / Retweet
tron-twitter like 1234567890
tron-twitter retweet 1234567890
```

## Output

JSON by default. Use `--format text` for human-readable output:

```bash
tron-twitter --format text search "OpenAI"
```

## Session Storage

Cookies and config stored in `~/.tron/twitter/`.
