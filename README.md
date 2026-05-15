# Ethics Spy 🔍

A multipurpose OSINT (Open Source Intelligence) tool for ethical security research,
personal data exposure assessment, and cybersecurity education.

**Developed by:** Ethicsware (Edward Arven)

---

## Features

### 🕵️ Spy Command — Username OSINT
- Scans 55 platforms simultaneously (GitHub, Reddit, Mastodon, Bluesky, Roblox, Pinterest, Etsy and more)
- Three scan modes:
  - **Single Scan** — detailed report for one username
  - **Bulk Scan** — scan up to 10 usernames at once
  - **Compare Mode** — compare two usernames side by side, highlights shared platforms
- Social Network Map — shared followers cross-platform, digital collective data, shared name/location/bio
- Roblox deep integration — Users API, Friends API (followers/following/friends count), Inventory API (collectible RAP value)
- API-verified results + manual verification links only for auth-required / JS-protected platforms

### 🔓 PWN Check — Email Breach Lookup
- Queries public breach databases (XposedOrNot, LeakCheck)
- Lists all breaches associated with the email
- Shows what data was exposed (password, IP, username, etc.)
- Risk level indicator (LOW / MEDIUM / HIGH)

### 📞 Phone Number Lookup
- International format support (+90, +1, +44, etc.)
- Country and region detection
- Carrier / operator identification via public numbering databases
- Covers 20+ countries with detailed carrier tables (TR, US, GB, DE, FR, RU, IN, CN and more)
- Line type detection (mobile, landline, toll-free)
- Timezone information

### 🌐 IP Lookup
- Geolocation (country, region, city, ZIP, coordinates)
- ISP and organization info
- ASN (Autonomous System Number)
- Reverse DNS lookup
- Proxy / VPN / hosting / mobile network detection
- Google Maps link for coordinates
- Shodan search link for open ports and services

### 🔎 Domain Lookup
- WHOIS / RDAP registration info (registrar, created, expires, DNSSEC)
- DNS records (resolved IPs, nameservers)
- MX records (mail servers)
- TXT records (SPF, DMARC)
- SSL certificate info (issuer, expiry date, days remaining)
- Subdomain enumeration via crt.sh (SSL certificate transparency logs)
- Hosting country and ISP detection

### 📧 Email Lookup — Account & Breach Finder
- Checks Gravatar, GitHub, Keybase for registered accounts
- Breach exposure check via XposedOrNot
- Manual verification links for 10 major platforms (Google, Microsoft, Instagram, LinkedIn, etc.)
- Displays linked usernames and display names where available

---

## Requirements

- Python 3.7+
- requests
- phonenumbers (optional, for enhanced phone lookup)

---

## Installation

```bash
pip install requests phonenumbers
```

---

## Usage

```bash
python ethics_spy.py
```



---

## Supported Platforms (Spy Command)

| Platform | Check Type |
|----------|-----------|
| GitHub | API |
| Reddit | API |
| Duolingo | API |
| Gravatar | API |
| Mastodon | API |
| Bluesky | API |
| Roblox | API (Users + Friends + Inventory) |
| Pastebin | Auto |
| Linktree | Auto |
| Steam | Auto |
| Medium | Auto |
| About.me | Auto |
| VK | Auto |
| Behance | Auto |
| Dribbble | Auto |
| Pinterest | Auto |
| SoundCloud | Auto |
| Flickr | Auto |
| Vimeo | Auto |
| DeviantArt | Auto |
| Tumblr | Auto |
| 500px | Auto |
| Letterboxd | Auto |
| Fiverr | Auto |
| BuyMeACoffee | Auto |
| Ko-fi | Auto |
| Disqus | Auto |
| WordPress | Auto |
| Archive.org | Auto |
| OpenSea | Auto |
| Telegram | Auto |
| Last.fm | Auto |
| Wattpad | Auto |
| Etsy | Auto |
| Substack | Auto |
| MyAnimeList | Auto |
| Poshmark | Auto |
| Clubhouse | Auto |
| Redbubble | Auto |
| Mixcloud | Auto |
| Giphy | Auto |
| ArtStation | Auto |
| eBay | Auto |
| Quora | Auto |
| Dailymotion | Auto |
| Rumble | Auto |
| Instagram | Manual |
| TikTok | Manual |
| Twitter / X | Manual |
| YouTube | Manual |
| Twitch | Manual |
| Snapchat | Manual |
| LinkedIn | Manual |
| Threads | Manual |
| Kick | Manual |

---

## Legal

This tool is intended for **legal OSINT research only**.

✅ Permitted use:
- Personal data exposure assessment (self-investigation)
- Cybersecurity education and awareness
- Ethical security research with proper authorization

❌ Prohibited use:
- Stalking, harassment, or surveillance without consent
- Any activity that violates local laws or privacy regulations (GDPR, KVKK, CCPA)

All data is retrieved exclusively from publicly available APIs and open sources.
The author assumes no responsibility for misuse.

See [LICENSE](LICENSE) for full terms.

---

> "With knowledge comes responsibility." — Ethicsware
