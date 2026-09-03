from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SECRETS = Path(r"c:\Users\neeli\kpkDevelopment\mts-new\.secrets")
CLIENT_CONFIG = SECRETS / "oauth-client.json"
TOKEN_PATH = SECRETS / "oauth-token.json"
SCOPES = ["https://www.googleapis.com/auth/drive"]


def main():
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_CONFIG), SCOPES)
    credentials = flow.run_local_server(port=0, access_type="offline", prompt="consent")
    TOKEN_PATH.write_text(credentials.to_json(), encoding="utf-8")
    print("OAUTH_REFRESH_PASS")


if __name__ == "__main__":
    main()