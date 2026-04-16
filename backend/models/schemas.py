import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
PHONE_REGEX = re.compile(r"^\+[1-9]\d{1,14}$")


class ScanRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    target: str = Field(min_length=3, max_length=254)
    target_type: Literal["email", "phone"]
    user_consent: bool

    @model_validator(mode="after")
    def validate_target_and_consent(self) -> "ScanRequest":
        if not self.user_consent:
            raise ValueError("Explicit user consent is legally required.")

        if self.target_type == "email" and not EMAIL_REGEX.fullmatch(self.target):
            raise ValueError("Invalid email format.")

        if self.target_type == "phone" and not PHONE_REGEX.fullmatch(self.target):
            raise ValueError("Phone must be in E.164 format (e.g., +1234567890).")

        return self


class ScanResponse(BaseModel):
    scan_id: str
    status: Literal["accepted", "complete", "failed"]
    message: str
