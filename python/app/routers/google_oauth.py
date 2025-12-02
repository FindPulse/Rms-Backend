from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse
import requests
import os
from dotenv import load_dotenv
from app.database.supabase_client import supabase

load_dotenv()

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
GOOGLE_REDIRECT_URI = os.getenv("REDIRECT_URI")
GOOGLE_SCOPE = "https://www.googleapis.com/auth/business.manage"

router = APIRouter(tags=["Google OAuth"])


@router.get("/connect_google")
def connect_google():
    """Redirect user to Google OAuth consent page."""
    oauth_url = (
        "https://accounts.google.com/o/oauth2/v2/auth"
        f"?client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        "&response_type=code"
        f"&scope={GOOGLE_SCOPE}"
        "&access_type=offline"
        "&prompt=consent"
    )
    return RedirectResponse(oauth_url)


@router.get("/oauth2callback")
def oauth2callback(request: Request):
    code = request.query_params.get("code")
    if not code:
        return {"error": "No code provided"}

    # Step 1 — Exchange code for token
    token_url = "https://oauth2.googleapis.com/token"
    data = {
        "code": code,
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "redirect_uri": GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    resp = requests.post(token_url, data=data)
    token_info = resp.json()

    access_token = token_info.get("access_token")
    refresh_token = token_info.get("refresh_token")

    # Step 2 — Fetch user's Google profile
    userinfo = requests.get(
        "https://www.googleapis.com/oauth2/v1/userinfo?alt=json",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    google_user_id = userinfo.get("id")
    google_email = userinfo.get("email")

    # Step 3 — Fetch Google Business Accounts
    gbp_accounts = requests.get(
        "https://mybusinessaccountmanagement.googleapis.com/v1/accounts",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()
    
    print("Google Business Accounts response:", gbp_accounts)

    accounts_list = gbp_accounts.get("accounts", [])
    if not accounts_list:
        return {"error": "No Google Business accounts found"}

    account_id = accounts_list[0]["name"]  # ex: accounts/123456789

    # Step 4 — Fetch Locations
    locations_resp = requests.get(
        f"https://mybusinessbusinessinformation.googleapis.com/v1/{account_id}/locations",
        headers={"Authorization": f"Bearer {access_token}"}
    ).json()

    locations = locations_resp.get("locations", [])

    # Step 5 — Save into Supabase
    supabase.table("google_accounts").upsert({
        "google_user_id": google_user_id,
        "email": google_email,
        "account_id": account_id,
        "locations": locations,
        "access_token": access_token,
        "refresh_token": refresh_token,
    }).execute()

    # Step 6 — Redirect frontend
    frontend_redirect = "http://localhost:3000/oauth-success"
    return RedirectResponse(frontend_redirect)
