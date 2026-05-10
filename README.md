# Ethics Spy 🔍

A multipurpose OSINT (Open Source Intelligence) tool for ethical security research,
personal data exposure assessment, and cybersecurity education.

**Developed by:** Ethicsware (Edward Arven)

---

## Features

### 🕵️ Spy Command — Username OSINT
- Scans 30+ platforms simultaneously (GitHub, Reddit, Chess.com, Lichess, TryHackMe and more)
- Three scan modes:
  - **Single Scan** — detailed report for one username
  - **Bulk Scan** — scan up to 10 usernames at once
  - **Compare Mode** — compare two usernames side by side, highlights shared platforms
- Social Network Map — detects shared name, location, and bio across platforms
- API-verified results + manual verification links for JS-protected platforms

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
| GitLab | API |
| Reddit | API |
| Chess.com | API |
| Lichess | API |
| HackerNews | API |
| Dev.to | API |
| Duolingo | API |
| Keybase | API |
| TryHackMe | API |
| Bitbucket | API |
| npm | API |
| Gravatar | API |
| PyPI | API |
| ProductHunt | HTTP |
| Pastebin | HTTP |
| Codecademy | HTTP |
| Linktree | HTTP |
| Instagram | Manual |
| TikTok | Manual |
| Twitter / X | Manual |
| YouTube | Manual |
| Twitch | Manual |
| Steam | Manual |
| Telegram | Manual |
| Spotify | Manual |
| Snapchat | Manual |
| Medium | Manual |
| Pinterest | Manual |
| Roblox | Manual |
| Replit | Manual |

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
