from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr
import uuid
import os
import requests

app = FastAPI(title="SaaS Business Auth")

# --- CORS for frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Production me frontend domain specify karo
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- In-memory DB (Demo) ---
yelp_businesses = [
    {"id": "b1", "name": "ABC Store", "email": "abc@business.com"},
    {"id": "b2", "name": "XYZ Cafe", "email": None},
]

pending_verifications = {}  # token -> {business_id, email, user_id}
verified_users = {}         # user_id -> list of verified business_ids
reviews_db = {
    "b1": [{"user": "John", "rating": 5, "comment": "Great!"}],
    "b2": [{"user": "Alice", "rating": 4, "comment": "Nice"}]
}

# --- Pydantic Models ---
class User(BaseModel):
    id: str
    email: EmailStr

class VerifyRequest(BaseModel):
    user_id: str
    business_id: str
    email: EmailStr

# --- Yelp API Setup ---
YELP_API_KEY = os.environ.get(
    "YELP_API_KEY",
    "Ir--EQE_Nh0dkn8bUac92vlLM9N-cIYQcd53BfU45xWQFIhdrPffY0xHJt3HxeWO3zMXxksU9flEloLemzbQHxJhc_U1AvyT--lyv7SusR2xU4oJ9yPffbj0vo8oaXYx"
)
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}

# --- Yelp Search (Real API) ---
@app.get("/yelp/search")
def search_business(term: str, location: str = "New York, NY", limit: int = 5):
    """
    Search businesses using real Yelp API
    """
    url = "https://api.yelp.com/v3/businesses/search"
    params = {"term": term, "location": location, "limit": limit}

    try:
        response = requests.get(url, headers=HEADERS, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        businesses = data.get("businesses", [])

        results = [
            {
                "id": b.get("id"),
                "name": b.get("name"),
                "rating": b.get("rating"),
                "review_count": b.get("review_count"),
                "location": b.get("location"),
                "phone": b.get("phone"),
                "url": b.get("url")
            }
            for b in businesses
        ]
        return {"businesses": results}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Yelp API request failed: {str(e)}")

# --- Request Verification ---
@app.post("/yelp/verify")
def request_verification(req: VerifyRequest):
    token = str(uuid.uuid4())
    pending_verifications[token] = {
        "business_id": req.business_id,
        "email": req.email,
        "user_id": req.user_id
    }
    print(f"[Demo] Verification link: http://localhost:8000/yelp/confirm/{token}")
    return {"message": "Verification email sent", "token": token}

# --- Confirm Verification ---
@app.get("/yelp/confirm/{token}")
def confirm_verification(token: str):
    if token not in pending_verifications:
        raise HTTPException(status_code=404, detail="Invalid token")
    
    data = pending_verifications.pop(token)
    user_id = data["user_id"]
    business_id = data["business_id"]

    if user_id not in verified_users:
        verified_users[user_id] = []
    verified_users[user_id].append(business_id)
    return {"message": f"Business {business_id} verified for user {user_id}"}

# --- Fetch Reviews ---
def check_verified_user(user_id: str, business_id: str):
    if user_id not in verified_users or business_id not in verified_users[user_id]:
        raise HTTPException(status_code=403, detail="Not authorized")
    return True

@app.get("/yelp/{business_id}/reviews")
def get_reviews(business_id: str, user_id: str):
    check_verified_user(user_id, business_id)
    return {"reviews": reviews_db.get(business_id, [])}
