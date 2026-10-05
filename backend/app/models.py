from datetime import datetime
from sqlalchemy import String, Text, JSON, DateTime, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from .db import Base

class Template(Base):
    __tablename__ = "templates"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    file_path: Mapped[str] = mapped_column(String(300))  # docxtpl .docx with {{placeholders}}
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    description: Mapped[str | None] = mapped_column(String(300), nullable=True)
    preview_image: Mapped[str | None] = mapped_column(String(300), nullable=True)
    signature_slots: Mapped[int] = mapped_column(Integer, default=2)
    default_left_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    default_right_role: Mapped[str | None] = mapped_column(String(120), nullable=True)
    updated_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

class Signatory(Base):
    __tablename__ = "signatories"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[str] = mapped_column(String(120))
    organization: Mapped[str] = mapped_column(String(160))
    signature_path: Mapped[str | None] = mapped_column(String(300), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

class Letter(Base):
    __tablename__ = "letters"
    id: Mapped[int] = mapped_column(primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("templates.id"))
    sender: Mapped[dict] = mapped_column(JSON)
    recipient: Mapped[dict] = mapped_column(JSON)
    through: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    subject: Mapped[str] = mapped_column(String(300))
    body: Mapped[str] = mapped_column(Text)
    signatory_ids: Mapped[list] = mapped_column(JSON, default=list)
    salutation: Mapped[str] = mapped_column(String(40), default="Respected Sir")
    font_size: Mapped[int] = mapped_column(Integer, default=11)
    font_name: Mapped[str] = mapped_column(String(40), default="Calibri")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Contact(Base):
    """Saved sender/through/recipient details for one-click autofill."""
    __tablename__ = "contacts"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    position: Mapped[str] = mapped_column(String(120))
    organization: Mapped[str] = mapped_column(String(160))
