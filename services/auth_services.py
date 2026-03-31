from models.users_model import User
from sqlalchemy.orm import Session

# signup
def signup_user(data, db: Session):

    existing = db.query(User).filter(User.email == data.email).first()
    if existing:
        return {"error": "Email already registered"}

    user = User(
        name=data.name,
        email=data.email,
        password=data.password,
        age=data.age

    )

    db.add(user)
    db.commit()

    return {"message": "User created successfully"}


# login
def login_user(data, db: Session):

    user = db.query(User).filter(
        User.email == data.email,
        User.password == data.password
    ).first()

    if not user:
        return {"error": "Invalid email or password"}

    return {
        "message": "Login successful",
        "user_id": user.id,
        "name": user.name
    }
