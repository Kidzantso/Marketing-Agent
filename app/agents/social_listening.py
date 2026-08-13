from __future__ import annotations

from app.models import SocialPost, now_iso


def run(competitors: list[str]) -> list[SocialPost]:
    posts: list[SocialPost] = []
    for competitor in competitors[:5]:
        slug = competitor.lower().replace(" ", "-")
        posts.extend(
            [
                SocialPost(
                    competitor=competitor,
                    platform="LinkedIn",
                    text=f"Everyone tracks competitors. Few teams know what changed before sales calls.",
                    post_url=f"https://public.example.com/{slug}/post-1",
                    posted_at=now_iso(),
                    engagement_signal="high comments",
                    format="text",
                ),
                SocialPost(
                    competitor=competitor,
                    platform="LinkedIn",
                    text=f"How would your team find out if {competitor} changed pricing tomorrow?",
                    post_url=f"https://public.example.com/{slug}/post-2",
                    posted_at=now_iso(),
                    engagement_signal="medium reactions",
                    format="carousel",
                ),
                SocialPost(
                    competitor=competitor,
                    platform="X",
                    text=f"We analyzed 120 market updates. The teams that win spot competitor moves first.",
                    post_url=f"https://public.example.com/{slug}/post-3",
                    posted_at=now_iso(),
                    engagement_signal="shared",
                    format="text",
                ),
            ]
        )
    return posts
