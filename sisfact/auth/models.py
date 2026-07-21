from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SisFactUser:
    user_id: int
    username: str
    display_name: str
    email: str | None
    role_code: str
    auth_type: str
    active: bool

    @classmethod
    def from_row(cls, row: Any) -> "SisFactUser":
        return cls(
            user_id=int(row[0]),
            username=str(row[1]),
            display_name=str(row[2] or row[1]),
            email=row[3],
            role_code=str(row[4]),
            auth_type=str(row[5]),
            active=str(row[6]).upper() == "Y",
        )

    def to_session(self) -> dict[str, Any]:
        return {
            "user_id": self.user_id,
            "username": self.username,
            "display_name": self.display_name,
            "email": self.email,
            "role_code": self.role_code,
            "auth_type": self.auth_type,
            "active": self.active,
        }
