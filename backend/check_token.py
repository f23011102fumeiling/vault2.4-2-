import jwt
from app.config.settings import settings

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ0ZWFjaGVyMDEiLCJyb2xlIjoidGVhY2hlciIsInVzZXJfaWQiOiI3NWJlNTgxMS0zOWU0LTQzYTUtYWFhOC0wNGY3YTJhNjg1ZTIiLCJleHAiOjE3Mzg5NDI4MjJ9.5kQZ6xL8zvJ8xN7yQ9kM0pL3nK5jR7sT2uV4wX6yZ8"

try:
    payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    print("JWT Token payload:")
    print(f"  user_id: {payload.get('user_id')}")
    print(f"  username: {payload.get('sub')}")
    print(f"  role: {payload.get('role')}")
    print(f"  exp: {payload.get('exp')}")
except Exception as e:
    print(f"Error decoding token: {e}")
