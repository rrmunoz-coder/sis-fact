from pathlib import Path
import sys
from getpass import getpass

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from sisfact import create_app
from sisfact.auth.ldap_auth import authenticate_ldap


def main():
    username = input("Usuario corporativo: ").strip()
    password = getpass("Password LDAP: ")

    app = create_app()
    with app.app_context():
        result = authenticate_ldap(username, password)
        print(result.status.value)
        if result.detail:
            print(result.detail)


if __name__ == "__main__":
    main()
