from __future__ import annotations

from configparser import ConfigParser

from sisfact.auth.models import SisFactUser
from sisfact.core.oracle import connect


USER_TABLE = "rm_cfact_user"


class UserRepository:
    def __init__(self, config: ConfigParser):
        self.config = config

    def find_by_username(self, username: str) -> SisFactUser | None:
        normalized = username.strip().lower()
        sql = f"""
            SELECT user_id, username, display_name, email, role_code, auth_type, active
            FROM {USER_TABLE}
            WHERE LOWER(username) = :username
        """
        with connect(self.config, "oracle") as conn:
            with conn.cursor() as cur:
                cur.execute(sql, username=normalized)
                row = cur.fetchone()
                return SisFactUser.from_row(row) if row else None

    def get_password_hash(self, username: str) -> str | None:
        normalized = username.strip().lower()
        sql = f"""
            SELECT password_hash
            FROM {USER_TABLE}
            WHERE LOWER(username) = :username
              AND active = 'Y'
        """
        with connect(self.config, "oracle") as conn:
            with conn.cursor() as cur:
                cur.execute(sql, username=normalized)
                row = cur.fetchone()
                return row[0] if row else None

    def create_user(
        self,
        username: str,
        display_name: str,
        email: str | None,
        role_code: str,
        auth_type: str = "LDAP",
        created_by: str = "SYSTEM",
    ) -> int:
        """Crea usuario local de autorización.

        No conecta contra LDAP. LDAP solo se usa al momento del login.
        """
        sql = f"""
            INSERT INTO {USER_TABLE} (
                username, display_name, email, role_code, auth_type, active, created_by
            ) VALUES (
                LOWER(:username), :display_name, :email, UPPER(:role_code), UPPER(:auth_type), 'Y', :created_by
            )
            RETURNING user_id INTO :user_id
        """
        with connect(self.config, "oracle") as conn:
            with conn.cursor() as cur:
                out_id = cur.var(int)
                cur.execute(
                    sql,
                    username=username.strip(),
                    display_name=display_name.strip(),
                    email=email,
                    role_code=role_code.strip(),
                    auth_type=auth_type.strip(),
                    created_by=created_by,
                    user_id=out_id,
                )
                conn.commit()
                return int(out_id.getvalue()[0])
