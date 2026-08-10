from getpass import getpass

from sisfact import create_app
from sisfact.auth.ldap_auth import authenticate_ldap

username = input("Usuario corporativo: ").strip()
password = getpass("Password LDAP: ")

app = create_app()
with app.app_context():
    result = authenticate_ldap(username, password)
    print(result.status.value)
    if result.detail:
        print(result.detail)
