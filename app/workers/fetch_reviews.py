import requests
import psycopg2
from textblob import TextBlob
from datetime import datetime
import json
from fastapi import FastAPI, HTTPException

# -------------------------
# DB Connection
# -------------------------
conn = psycopg2.connect(
    dbname="postgres",
    user="postgres",
    password="Starry@Night#^123",
    host="db.ycnvdwnsvwgzyvdtgndq.supabase.co",
    port=5432
)

# -------------------------
# FastAPI App (Optional for Admin Toggle)
# -------------------------
app = FastAPI()

@app.patch("/toggle_client/{client_id}")
def toggle_client(client_id: str):
    cur = conn.cursor()
    cur.execute("""
        UPDATE clients SET is_active = NOT is_active WHERE id = %s
    """, (client_id,))
    conn.commit()
    cur.close()
    return {"status": "success", "message": f"Client {client_id} toggled successfully"}

# -------------------------
# NLP Sentiment
# -------------------------
def calculate_sentiment(text: str):
    if not text:
        return {"polarity": 0.0, "subjectivity": 0.0, "sentiment_label": "neutral"}
    
    analysis = TextBlob(text)
    polarity = analysis.sentiment.polarity
    subjectivity = analysis.sentiment.subjectivity
    
    if polarity > 0:
        label = "positive"
    elif polarity < 0:
        label = "negative"
    else:
        label = "neutral"
    
    return {"polarity": polarity, "subjectivity": subjectivity, "sentiment_label": label}

# -------------------------
# Refresh Access Token (Placeholder)
# -------------------------
def refresh_access_token(refresh_token):
    # TODO: Implement Google OAuth refresh token logic if needed
    return None  # Replace with actual refreshed access token

# -------------------------
# Fetch Google Reviews
# -------------------------
def fetch_google_reviews(google_account_id, access_token):
    url = f"https://mybusinessbusinessinformation.googleapis.com/v1/{google_account_id}/reviews"
    headers = {"Authorization": f"Bearer {access_token}"}
    
    resp = requests.get(url, headers=headers)
    if resp.status_code != 200:
        print(f"Failed to fetch reviews for {google_account_id}: {resp.text}")
        return []
    
    return resp.json().get("reviews", [])

# -------------------------
# Bulk Insert Reviews
# -------------------------
def bulk_insert_reviews(reviews, client_id):
    cur = conn.cursor()
    inserted_count = 0
    for r in reviews:
        try:
            nlp_sentiment = calculate_sentiment(r.get("comment", ""))
            cur.execute("""
                INSERT INTO google_reviews (
                    location_id, review_id, author_name, rating, comment,
                    create_time, raw, nlp_sentiment, inserted_at, client_id
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (review_id) DO NOTHING
            """, (
                r.get("location_id"),
                r.get("review_id"),
                r.get("author_name"),
                r.get("rating"),
                r.get("comment"),
                r.get("create_time"),
                json.dumps(r.get("raw")),
                json.dumps(nlp_sentiment),
                datetime.now(),
                client_id
            ))
            inserted_count += 1
        except Exception as e:
            print(f"Error inserting review {r.get('review_id')}: {e}")
    conn.commit()
    cur.close()
    print(f"Inserted {inserted_count} reviews for client {client_id}")

# -------------------------
# Main Function: Multi-Client Fetch
# -------------------------
def main():
    cur = conn.cursor()
    # ✅ Join using client_id in tokens
    cur.execute("""
        SELECT c.id, t.access_token, t.refresh_token, t.google_account_id
        FROM clients c
        JOIN google_tokens t ON t.client_id = c.id
        WHERE c.is_active = TRUE
    """)
    active_clients = cur.fetchall()
    cur.close()

    print(f"Found {len(active_clients)} active clients")

    for client_id, access_token, refresh_token, google_account_id in active_clients:
        print(f"Processing client: {client_id}")
        if not access_token:
            access_token = refresh_access_token(refresh_token)

        reviews = fetch_google_reviews(google_account_id, access_token)
        if reviews:
            mapped_reviews = []
            for r in reviews:
                mapped_reviews.append({
                    "location_id": r.get("locationId"),
                    "review_id": r.get("reviewId"),
                    "author_name": r.get("reviewer", {}).get("displayName"),
                    "rating": r.get("starRating"),
                    "comment": r.get("comment"),
                    "create_time": r.get("createTime"),
                    "raw": r
                })
            bulk_insert_reviews(mapped_reviews, client_id)
        else:
            print(f"No reviews found for client {client_id}")

if __name__ == "__main__":
    main()
