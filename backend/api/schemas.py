from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    status: str
    applied_at: datetime | None = None
    notes: str = ""


class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    title: str
    company: str
    location: str
    remote: bool
    url: str
    source: str
    description: str = ""
    posted_at: datetime | None
    fetched_at: datetime | None = None
    is_software: bool
    score: int
    application: ApplicationOut | None = None


class ManualJobIn(BaseModel):
    """For WhatsApp/LinkedIn posts you paste in by hand."""
    title: str
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    source: str = "manual"


class ApplicationIn(BaseModel):
    status: str = "saved"  # saved | applied | interview | rejected | offer
    notes: str = ""
