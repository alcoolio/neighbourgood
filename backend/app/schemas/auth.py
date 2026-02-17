"""Pydantic schemas for authentication."""

from pydantic import BaseModel


class UserRegister(BaseModel):
    email: str
    password: str
    display_name: str
    neighbourhood: str | None = None


class UserLogin(BaseModel):
    email: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
