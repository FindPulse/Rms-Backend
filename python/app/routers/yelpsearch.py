from fastapi import APIRouter, HTTPException, Query
import requests
import os

router = APIRouter()

# --- Yelp API Key ---
YELP_API_KEY = os.environ.get(
    "YELP_API_KEY",
    "Ir--EQE_Nh0dkn8bUac92vlLM9N-cIYQcd53BfU45xWQFIhdrPffY0xHJt3HxeWO3zMXxksU9flEloLemzbQHxJhc_U1AvyT--lyv7SusR2xU4oJ9yPffbj0vo8oaXYx"
)
HEADERS = {"Authorization": f"Bearer {YELP_API_KEY}"}


@router.get("/search")
def search_yelp(
    term: str = Query(..., description="Business name or search term"),
    location: str = Query("New York, NY", description="City and State, e.g., New York, NY"),
    limit: int = Query(5, ge=1, le=50, description="Number of results")
):
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
