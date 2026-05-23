"""Parses Slack channel export JSON into a SlackExport struct."""
import json
from pathlib import Path
from redactor.models import Message, SlackExport, UserProfile


def parse(json_path: str) -> SlackExport:
    channel_name = Path(json_path).stem
    with open(json_path) as f:
        raw_messages = json.load(f)

    users: dict[str, UserProfile] = {}
    messages: list[Message] = []

    for raw in raw_messages:
        profile = _parse_profile(raw)
        user_id = raw.get("user")
        if profile and user_id and user_id not in users:
            users[user_id] = profile

        messages.append(Message(
            ts=raw.get("ts", ""),
            text=raw.get("text", ""),
            user_id=user_id,
            user_profile=profile,
            bot_id=raw.get("bot_id"),
            bot_username=raw.get("username") if raw.get("bot_id") else None,
        ))

    return SlackExport(channel_name=channel_name, messages=messages, users=users)


def _parse_profile(raw: dict) -> UserProfile | None:
    p = raw.get("user_profile")
    user_id = raw.get("user")
    if not p or not user_id:
        return None
    return UserProfile(
        user_id=user_id,
        real_name=p.get("real_name", ""),
        display_name=p.get("display_name", ""),
        first_name=p.get("first_name", ""),
        username=p.get("name", ""),
        title=p.get("title", ""),
        avatar_hash=p.get("avatar_hash", ""),
        image_url=p.get("image_72", ""),
    )
