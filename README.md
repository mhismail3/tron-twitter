# tron-twitter

Twitter/X CLI for the Tron agent. Wraps [twikit](https://github.com/d60/twikit) for search, trending, timelines, notifications, DMs, and posting — no API keys required.

**Stateless by design.** Every invocation reads credentials from environment variables and writes nothing to disk. The caller owns credential storage (e.g. the Tron vault).

## Install

```bash
brew install mhismail3/tools/tron-twitter
```

Or from source:

```bash
pip install .
```

## Interface

Two environment variables drive everything:

| Variable | When | Format |
|----------|------|--------|
| `TRON_TWITTER_COOKIES` | Every command | JSON object: `{"auth_token": "...", "ct0": "..."}` |
| `TRON_TWITTER_STATE`   | `check-mentions`, `check-dms` only | JSON object: `{"last_mention_ts": 0, "last_dm_ts": "0"}` |

`check-mentions` and `check-dms` return a two-part envelope so the caller can persist the new bookmark:

```json
{
  "items": [ /* new mentions or DMs since the bookmark */ ],
  "state": { "last_mention_ts": 1728000000000 }
}
```

With `--peek`, `state` is unchanged (the bookmark does not advance).

## Cold start

There is no interactive login. The `auth_token` and `ct0` values must be harvested from a real browser session where you are already signed into x.com:

1. Open https://x.com in your browser
2. DevTools → Application (Chrome/Edge) or Storage (Firefox/Safari) → Cookies → `https://x.com`
3. Copy the values of `auth_token` and `ct0`
4. Hand them to your caller (the Tron vault, an env file, etc.)

Automated logins trip X/Twitter's bot detection; don't bother.

## Usage

```bash
# Export cookies once for the session, or inline per command.
export TRON_TWITTER_COOKIES='{"auth_token":"...","ct0":"..."}'

# Read operations
tron-twitter search "AI agents" --count 20 --product Top
tron-twitter trending --category trending
tron-twitter timeline elonmusk --count 10
tron-twitter user elonmusk
tron-twitter tweet 1234567890
tron-twitter notifications --type Mentions
tron-twitter dms
tron-twitter dm-history elonmusk --count 20

# Stateful — pass state in, persist state out
OUT=$(TRON_TWITTER_STATE='{"last_mention_ts":0}' tron-twitter check-mentions)
echo "$OUT" | jq '.items'
NEW_STATE=$(echo "$OUT" | jq -c '.state')
# → persist $NEW_STATE wherever you keep state

# Preview without advancing the bookmark
tron-twitter check-mentions --peek

# Write operations
tron-twitter post "Hello from Tron"
tron-twitter reply 1234567890 "Great tweet!"
tron-twitter like 1234567890
tron-twitter retweet 1234567890
tron-twitter follow elonmusk
tron-twitter dm elonmusk "Hi"

# Validate cookies
tron-twitter auth status
```

## Output

JSON by default (one document per command). Use `--format text` for human-readable output on read commands:

```bash
tron-twitter --format text search "OpenAI"
```

`check-mentions` and `check-dms` always emit the JSON envelope regardless of `--format`, because there's no sensible text rendering for a two-part structure.

## Why environment variables?

- **Stateless.** No `~/.tron/` writes, no config files, no path assumptions.
- **Per-call scoping.** Inline `VAR=value cmd` invocations don't leak credentials into the rest of the shell.
- **Vault-friendly.** Credential managers like the Tron vault can decrypt → pipe → `trap` cleanup without ever touching the filesystem.
- **Single source of truth.** The caller decides where cookies live; the CLI doesn't have an opinion.

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Runtime error (API failure, bad argument, missing/invalid env var) |
