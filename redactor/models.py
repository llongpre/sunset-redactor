from dataclasses import dataclass, field
from enum import StrEnum



class PIIKind(StrEnum):
    PERSON = "PERSON"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    SSN = "SSN"
    TAX_ID = "TAX_ID"
    CREDIT_CARD = "CREDIT_CARD"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    ROUTING_NUMBER = "ROUTING_NUMBER"
    API_TOKEN = "API_TOKEN"
    IP_ADDRESS = "IP_ADDRESS"
    PASSPORT = "PASSPORT"
    AGE = "AGE"
    SLACK_USER_ID = "SLACK_USER_ID"
    AVATAR_HASH = "AVATAR_HASH"
    ADDRESS = "ADDRESS"


@dataclass
class Match:
    start: int
    end: int
    kind: PIIKind
    value: str


@dataclass
class Entity:
    value: str
    kind: PIIKind
    placeholder: str


@dataclass
class UserProfile:
    user_id: str
    real_name: str = ""
    display_name: str = ""
    first_name: str = ""
    username: str = ""
    title: str = ""
    avatar_hash: str = ""
    image_url: str = ""


@dataclass
class Message:
    ts: str
    text: str
    user_id: str | None = None
    user_profile: UserProfile | None = None
    bot_id: str | None = None
    bot_username: str | None = None

    @property
    def is_bot(self) -> bool:
        return self.bot_id is not None

    def text_fields(self) -> list[tuple[str, str]]:
        """Returns (field_name, value) pairs for all text fields worth scanning."""
        fields = [("text", self.text)]
        if self.user_profile:
            p = self.user_profile
            for key, val in [
                ("real_name", p.real_name),
                ("display_name", p.display_name),
                ("first_name", p.first_name),
                ("username", p.username),
                ("title", p.title),
            ]:
                if val:
                    fields.append((f"user_profile.{key}", val))
        return fields


@dataclass
class SlackExport:
    channel_name: str
    messages: list[Message] = field(default_factory=list)
    users: dict[str, UserProfile] = field(default_factory=dict)


@dataclass
class PDFPage:
    page_num: int
    text: str


@dataclass
class PDFDocument:
    filename: str
    pages: list[PDFPage] = field(default_factory=list)


@dataclass
class MarkdownSection:
    heading: str  # heading line e.g. "## Team Bios"; empty string for pre-heading content
    level: int    # heading depth 1–6; 0 for pre-heading content
    text: str     # full section text including the heading line


@dataclass
class MarkdownDocument:
    filename: str
    sections: list[MarkdownSection] = field(default_factory=list)
