from __future__ import annotations

from app.models import PublicPage, SocialPost, now_iso


def run(competitors: list[str], pages: list[PublicPage] | None = None) -> list[SocialPost]:
    posts: list[SocialPost] = []
    for page in pages or []:
        if page.error or not page.text or page.competitor not in competitors:
            continue
        platform = {"linkedin": "LinkedIn", "x": "X", "twitter": "X"}.get(page.label.lower(), "Website")
        text = page.title or page.text[:280]
        if not text:
            continue
        posts.append(
            SocialPost(
                competitor=page.competitor,
                platform=platform,
                text=text,
                post_url=page.url,
                posted_at=page.scraped_at or now_iso(),
                engagement_signal=None,
                format="text",
            )
        )
    return posts
