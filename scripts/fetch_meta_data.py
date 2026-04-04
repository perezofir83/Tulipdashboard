#!/usr/bin/env python3
"""
Fetch Meta data: Ads, Facebook Page, Instagram
Sends CSV reports to email via Gmail, or saves locally.

Usage:
  python3 scripts/fetch_meta_data.py          # save to data/live/
  python3 scripts/fetch_meta_data.py --email   # also send via email
"""

import os, sys, json, csv, io, smtplib
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    os.system(f"{sys.executable} -m pip install requests -q")
    import requests

# Load .env
ENV_PATH = Path(__file__).parent.parent / ".env"
if ENV_PATH.exists():
    for line in ENV_PATH.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, val = line.split("=", 1)
            os.environ.setdefault(key.strip(), val.strip())

ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
PAGE_ACCESS_TOKEN = ""  # Will be fetched automatically
PAGE_ID = os.environ.get("META_PAGE_ID", "126730374027916")
IG_ID = os.environ.get("META_IG_ID", "17841400317118872")
AD_ACCOUNT_ID = os.environ.get("META_AD_ACCOUNT_ID", "")
BASE_URL = "https://graph.facebook.com/v23.0"
DATA_DIR = Path(__file__).parent.parent / "data" / "live"


def get_page_token():
    """Get Page Access Token from User Access Token."""
    global PAGE_ACCESS_TOKEN
    r = requests.get(f"{BASE_URL}/{PAGE_ID}", params={
        "fields": "access_token",
        "access_token": ACCESS_TOKEN,
    })
    r.raise_for_status()
    PAGE_ACCESS_TOKEN = r.json().get("access_token", ACCESS_TOKEN)
    print(f"  Got Page Access Token")
    return PAGE_ACCESS_TOKEN

def api_get(endpoint, params=None):
    """Make a GET request to Graph API."""
    p = {"access_token": ACCESS_TOKEN}
    if params:
        p.update(params)
    r = requests.get(f"{BASE_URL}/{endpoint}", params=p)
    r.raise_for_status()
    return r.json()

def paginate(endpoint, params=None):
    """Paginate through all results."""
    all_data = []
    p = {"access_token": ACCESS_TOKEN, "limit": 100}
    if params:
        p.update(params)
    url = f"{BASE_URL}/{endpoint}"
    while url:
        r = requests.get(url, params=p)
        r.raise_for_status()
        data = r.json()
        all_data.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        p = {}  # params are in the next URL
    return all_data


# ─── META ADS ───────────────────────────────────────────

def get_active_ads(act_id):
    """Get set of truly active ad names — only where campaign + ad set + ad are ALL active."""
    try:
        data = paginate(
            f"act_{act_id}/ads",
            {
                "fields": "name,effective_status,campaign{name},adset{name}",
                "filtering": json.dumps([{"field": "effective_status", "operator": "IN", "value": ["ACTIVE"]}]),
            },
        )
        # Build lookup: (campaign_name, adset_name, ad_name) → truly active
        active_keys = set()
        active_campaigns = set()
        for ad in data:
            c_name = ad.get("campaign", {}).get("name", "")
            as_name = ad.get("adset", {}).get("name", "")
            ad_name = ad.get("name", "")
            active_keys.add((c_name, as_name, ad_name))
            active_campaigns.add(c_name)
        print(f"  Truly active: {len(active_keys)} ads in {len(active_campaigns)} campaigns")
        for c in active_campaigns:
            print(f"    ✅ {c}")
        return active_keys
    except Exception as e:
        print(f"  Could not fetch ad statuses: {e}")
        return None  # None = don't filter


def fetch_meta_ads(active_only=True):
    """Fetch ad campaign performance for last 7 days."""
    if AD_ACCOUNT_ID:
        act_id = AD_ACCOUNT_ID
    else:
        try:
            me = api_get("me", {"fields": "adaccounts{account_id,name}"})
            accounts = me.get("adaccounts", {}).get("data", [])
            if not accounts:
                print("No ad accounts found")
                return None
            act_id = accounts[0]["account_id"]
            print(f"Using ad account: {accounts[0].get('name', act_id)}")
        except Exception as e:
            print(f"Could not find ad account: {e}")
            return None

    # Get truly active ads (campaign+adset+ad all ACTIVE)
    active_keys = get_active_ads(act_id) if active_only else None

    today = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    try:
        data = paginate(
            f"act_{act_id}/insights",
            {
                "fields": "campaign_name,adset_name,ad_name,impressions,reach,clicks,spend,actions,cost_per_action_type,ctr,cpc,frequency",
                "time_range": json.dumps({"since": week_ago, "until": today}),
                "level": "ad",
                "time_increment": 1,
                "limit": 500,
            },
        )
    except Exception as e:
        print(f"Meta Ads API error: {e}")
        return None

    if not data:
        print("No Meta Ads data")
        return None

    rows = []
    skipped = 0
    for row in data:
        campaign_name = row.get("campaign_name", "")
        adset_name = row.get("adset_name", "")
        ad_name = row.get("ad_name", "")

        # Filter: only truly active (campaign + ad set + ad all ACTIVE)
        if active_keys is not None and (campaign_name, adset_name, ad_name) not in active_keys:
            skipped += 1
            continue

        # Extract results from actions
        results = 0
        result_type = ""
        cost_per_result = 0
        actions = row.get("actions", [])
        if actions:
            results = int(actions[0].get("value", 0))
            result_type = actions[0].get("action_type", "")
        cpa = row.get("cost_per_action_type", [])
        if cpa:
            cost_per_result = float(cpa[0].get("value", 0))

        rows.append({
            "Day": row.get("date_start", ""),
            "Campaign name": campaign_name,
            "Ad set name": row.get("adset_name", ""),
            "Ad name": row.get("ad_name", ""),
            "Impressions": row.get("impressions", 0),
            "Reach": row.get("reach", 0),
            "Frequency": row.get("frequency", 0),
            "Result type": result_type,
            "Results": results,
            "Amount spent (ILS)": row.get("spend", 0),
            "Cost per result": cost_per_result,
        })

    if skipped:
        print(f"  Skipped {skipped} rows from paused campaigns")

    return write_csv("meta_ads.csv", rows)


# ─── FACEBOOK PAGE ──────────────────────────────────────

def fetch_facebook_organic():
    """Fetch Facebook page posts and their engagement."""
    # Use Page Token for page data
    token = PAGE_ACCESS_TOKEN or ACCESS_TOKEN
    all_posts = []
    url = f"{BASE_URL}/{PAGE_ID}/published_posts"
    params = {
        "access_token": token,
        "fields": "message,created_time,shares",
        "since": (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d"),
        "limit": 100,
    }
    while url:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        all_posts.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = {}

    if not all_posts:
        print("No Facebook posts found")
        return None

    rows = []
    for post in all_posts:
        post_id = post.get("id", "")
        message = (post.get("message") or "")[:100].replace("\n", " ")
        created = post.get("created_time", "")[:10]
        shares = post.get("shares", {}).get("count", 0)

        # Get post insights separately
        impressions = 0
        reach = 0
        clicks = 0
        try:
            ins = requests.get(
                f"{BASE_URL}/{post_id}/insights",
                params={
                    "access_token": token,
                    "metric": "post_impressions,post_impressions_unique,post_clicks",
                }
            ).json()
            for metric in ins.get("data", []):
                name = metric.get("name", "")
                val = metric.get("values", [{}])[0].get("value", 0)
                if name == "post_impressions":
                    impressions = val
                elif name == "post_impressions_unique":
                    reach = val
                elif name == "post_clicks":
                    clicks = val
        except:
            pass

        # Get likes/reactions count
        likes = 0
        comments_count = 0
        try:
            engagement = requests.get(
                f"{BASE_URL}/{post_id}",
                params={
                    "access_token": token,
                    "fields": "likes.summary(true).limit(0),comments.summary(true).limit(0)",
                }
            ).json()
            likes = engagement.get("likes", {}).get("summary", {}).get("total_count", 0)
            comments_count = engagement.get("comments", {}).get("summary", {}).get("total_count", 0)
        except:
            pass

        rows.append({
            "Date": created,
            "Platform": "Facebook",
            "Post": message,
            "Impressions": impressions,
            "Reach": reach,
            "Likes": likes,
            "Comments": comments_count,
            "Shares": shares,
            "Clicks": clicks,
            "Engagement": likes + comments_count + shares,
        })

    return write_csv("social_facebook.csv", rows)


# ─── INSTAGRAM ──────────────────────────────────────────

def fetch_instagram_organic():
    """Fetch Instagram posts and their engagement."""
    token = PAGE_ACCESS_TOKEN or ACCESS_TOKEN
    all_media = []
    url = f"{BASE_URL}/{IG_ID}/media"
    params = {
        "access_token": token,
        "fields": "caption,timestamp,media_type,like_count,comments_count",
        "limit": 50,
    }
    while url:
        r = requests.get(url, params=params)
        r.raise_for_status()
        data = r.json()
        all_media.extend(data.get("data", []))
        url = data.get("paging", {}).get("next")
        params = {}
    # Filter to last 30 days
    cutoff = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    media = [m for m in all_media if m.get("timestamp", "")[:10] >= cutoff]

    if not media:
        print("No Instagram posts found")
        return None

    rows = []
    for post in media:
        caption = (post.get("caption") or "")[:100].replace("\n", " ")
        created = post.get("timestamp", "")[:10]
        likes = post.get("like_count", 0)
        comments = post.get("comments_count", 0)
        media_type = post.get("media_type", "")

        # Get insights per post
        impressions = 0
        reach = 0
        saved = 0
        shares = 0
        post_id = post.get("id", "")
        try:
            ins = requests.get(
                f"{BASE_URL}/{post_id}/insights",
                params={
                    "access_token": token,
                    "metric": "impressions,reach,saved,shares",
                }
            ).json()
            for metric in ins.get("data", []):
                name = metric.get("name", "")
                val = metric.get("values", [{}])[0].get("value", 0)
                if name == "impressions":
                    impressions = val
                elif name == "reach":
                    reach = val
                elif name == "saved":
                    saved = val
                elif name == "shares":
                    shares = val
        except:
            pass

        rows.append({
            "Date": created,
            "Platform": "Instagram",
            "Type": media_type,
            "Post": caption,
            "Impressions": impressions,
            "Reach": reach,
            "Likes": likes,
            "Comments": comments,
            "Shares": shares,
            "Saved": saved,
            "Engagement": likes + comments + shares + saved,
        })

    return write_csv("social_instagram.csv", rows)


# ─── HELPERS ────────────────────────────────────────────

def write_csv(filename, rows):
    """Merge new rows into existing CSV file (append + deduplicate)."""
    if not rows:
        return None
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = DATA_DIR / filename

    headers = list(rows[0].keys())

    # Dedup keys per file type
    dedup_map = {
        "meta_ads.csv": ["Day", "Campaign name", "Ad set name", "Ad name"],
        "social_facebook.csv": ["Date", "Post"],
        "social_instagram.csv": ["Date", "Post"],
    }
    keys = dedup_map.get(filename, [])

    def row_key(row):
        return tuple(str(row.get(k, "")) for k in keys) if keys else tuple(row.values())

    # Load existing rows
    existing_rows = []
    if filepath.exists():
        with open(filepath, "r", encoding="utf-8") as f:
            existing_rows = list(csv.DictReader(f))

    existing_keys = {row_key(r) for r in existing_rows}

    # Append only new rows
    added = 0
    for row in rows:
        rk = row_key(row)
        if rk not in existing_keys:
            existing_rows.append(row)
            existing_keys.add(rk)
            added += 1

    # Sort by date (first column)
    date_col = headers[0]
    existing_rows.sort(key=lambda r: r.get(date_col, ""), reverse=True)

    # Write merged result
    with open(filepath, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(existing_rows)

    print(f"  {filename}: {len(existing_rows)} total rows ({added} new)")
    return filepath


def refresh_long_lived_token():
    """Exchange short-lived token for long-lived (60 days), or refresh existing long-lived token."""
    global ACCESS_TOKEN
    app_id = os.environ.get("META_APP_ID", "")
    app_secret = os.environ.get("META_APP_SECRET", "")
    if not app_secret:
        print("  SKIP: META_APP_SECRET not set in .env (token will expire)")
        return

    try:
        r = requests.get(f"{BASE_URL}/oauth/access_token", params={
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": ACCESS_TOKEN,
        })
        r.raise_for_status()
        data = r.json()
        new_token = data.get("access_token", "")
        if new_token and new_token != ACCESS_TOKEN:
            ACCESS_TOKEN = new_token
            # Update .env file
            env_text = ENV_PATH.read_text()
            lines = env_text.splitlines()
            new_lines = []
            for line in lines:
                if line.startswith("META_ACCESS_TOKEN="):
                    new_lines.append(f"META_ACCESS_TOKEN={new_token}")
                else:
                    new_lines.append(line)
            ENV_PATH.write_text("\n".join(new_lines) + "\n")
            expires_in = data.get("expires_in", 0)
            days = expires_in // 86400 if expires_in else "?"
            print(f"  Token refreshed! Expires in {days} days")
        else:
            print("  Token already long-lived or unchanged")
    except Exception as e:
        print(f"  Token refresh failed: {e}")


def main():
    if not ACCESS_TOKEN or ACCESS_TOKEN == "PASTE_YOUR_TOKEN_HERE":
        print("ERROR: Set META_ACCESS_TOKEN in .env file")
        sys.exit(1)

    print("=== Fetching Meta Data ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()

    print("0. Refreshing token...")
    refresh_long_lived_token()
    print()

    print("1. Getting Page Token...")
    get_page_token()
    print()

    print("2. Meta Ads...")
    fetch_meta_ads()
    print()

    print("3. Facebook Page...")
    fetch_facebook_organic()
    print()

    print("4. Instagram...")
    fetch_instagram_organic()
    print()

    print("=== Done! ===")


if __name__ == "__main__":
    main()
