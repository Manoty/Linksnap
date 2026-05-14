# analytics/parsers.py
# Lightweight request metadata parsers.
# Kept separate from the service so each parser is independently testable
# and swappable without touching business logic.
#
# Phase 5 adds: GeoIP2 for country/city lookup.

import re


def parse_device_type(user_agent: str) -> str:
    """
    Classifies a user agent string into a device category.
    Returns one of: 'mobile', 'tablet', 'bot', 'desktop', ''

    Deliberately simple — this covers 95% of real traffic.
    Replace with user-agents library for production-grade parsing.
    """
    if not user_agent:
        return ''

    ua = user_agent.lower()

    BOT_PATTERNS = [
        'bot', 'crawler', 'spider', 'slurp', 'facebookexternalhit',
        'twitterbot', 'linkedinbot', 'whatsapp', 'telegrambot',
        'googlebot', 'bingbot', 'curl', 'python-requests', 'axios',
    ]
    if any(p in ua for p in BOT_PATTERNS):
        return 'bot'

    TABLET_PATTERNS = ['ipad', 'tablet', 'kindle', 'playbook']
    if any(p in ua for p in TABLET_PATTERNS):
        return 'tablet'

    MOBILE_PATTERNS = ['mobile', 'android', 'iphone', 'ipod', 'blackberry', 'windows phone']
    if any(p in ua for p in MOBILE_PATTERNS):
        return 'mobile'

    return 'desktop'


def extract_ip(request) -> str | None:
    """
    Extracts the real client IP from a Django request.
    Handles reverse proxy headers (nginx, Cloudflare, load balancers).
    X-Forwarded-For can be spoofed on the public internet — in production
    this should be restricted to trusted proxy IPs only.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # X-Forwarded-For: client, proxy1, proxy2
        # Take the leftmost (original client)
        ip = x_forwarded_for.split(',')[0].strip()
        return ip
    return request.META.get('REMOTE_ADDR')