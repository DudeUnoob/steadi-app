import jwt
import time
import uuid
from datetime import datetime, timedelta

# This is just a mock JWT for testing
user_data = {
    "id": "test-user-id-123456",  # Supabase ID
    "email": "supabase-test@steadi.com",
    "user_metadata": {
        "role": "owner"
    }
}

# Print the payload for easier curl usage
print("Payload (for curl):")
print(f"{user_data}")

# Generate a token with no signature validation
print("\nUnsigned token for testing:")
print("Bearer " + jwt.encode(user_data, "", algorithm="none")) 