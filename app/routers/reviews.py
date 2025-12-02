from fastapi import APIRouter, HTTPException
from app.database.supabase_client import supabase
import requests
import os

router = APIRouter(prefix="/reviews", tags=["Google Reviews"])

GOOGLE_REVIEW_URL = "https://mybusiness.googleapis.com/v4"

def refresh_access_token(refresh_token):
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    r = requests.post(url, data=data).json()
    return r.get("access_token")


@router.get("/{location_id}")
def get_reviews(location_id: str, user_email: str):
    """
    user_email is passed from frontend OR extracted from JWT
    """

    # 1. Load user’s Google account data
    result = supabase.table("google_accounts") \
        .select("*") \
        .eq("email", user_email) \
        .execute()

    if not result.data:
        raise HTTPException(404, "Google account not connected")

    google_row = result.data[0]

    account_id = google_row["account_id"]  # accounts/1234
    access_token = google_row["access_token"]
    refresh_token = google_row["refresh_token"]

    # 2. Try API call with current access token
    reviews_api = (
        f"https://mybusiness.googleapis.com/v4/{account_id}/locations/{location_id}/reviews"
    )

    headers = {"Authorization": f"Bearer {access_token}"}
    r = requests.get(reviews_api, headers=headers)

    # 3. If token expired → refresh + retry
    if r.status_code == 401:
        access_token = refresh_access_token(refresh_token)

        # update in supabase
        supabase.table("google_accounts").update({
            "access_token": access_token
        }).eq("email", user_email).execute()

        headers = {"Authorization": f"Bearer {access_token}"}
        r = requests.get(reviews_api, headers=headers)  # retry

    if r.status_code != 200:
        raise HTTPException(400, "Failed to fetch reviews")

    return r.json()

@router.get("/locations")
def get_locations(user_email: str):
    result = supabase.table("google_accounts") \
        .select("locations") \
        .eq("email", user_email) \
        .execute()

    if not result.data:
        raise HTTPException(404, "No connected Google account")

    return result.data[0]["locations"]
