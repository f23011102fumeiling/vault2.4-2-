from app.database import SessionLocal
from app.models.user import User

db = SessionLocal()
users = db.query(User).all()
print('Current users in database:')
for u in users:
    print(f'  - ID: {u.id}, Username: {u.username}, Role: {u.role}')
db.close()
