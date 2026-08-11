from datetime import timedelta

from app.core.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    get_password_hash,
    verify_password,
)
from app.db.models import Tenant, User, get_db
from app.models.schemas import UserCreate
from fastapi import APIRouter, Depends, Header, HTTPException
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
    OAuth2PasswordRequestForm,
)
from jose import JWTError, jwt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

router = APIRouter(prefix="/auth", tags=["auth"])

security = HTTPBearer()


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    token = credentials.credentials

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])

        tenant_id = payload.get("tenant_id")

        if tenant_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token: tenant_id missing",
            )

        return tenant_id

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token",
        )


@router.post("/signup")
async def signup(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    # 1. Fetch tenant asynchronously using SQLAlchemy 2.0 syntax
    result = await db.execute(
        select(Tenant).where(Tenant.name == user_data.tenant_name)
    )
    tenant = result.scalars().first()

    # 2. Create tenant if it doesn't exist
    if not tenant:
        tenant = Tenant(name=user_data.tenant_name)
        db.add(tenant)
        await db.flush()  # flush() gets the ID without closing the transaction

    # 3. Check if user exists asynchronously
    user_result = await db.execute(select(User).where(User.email == user_data.email))
    existing_user = user_result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    # 4. Create user
    new_user = User(
        email=user_data.email,
        hashed_password=get_password_hash(user_data.password),
        tenant_id=tenant.id,
    )
    db.add(new_user)

    # Commit is handled automatically by the get_db dependency on success
    return {"message": "User created successfully", "tenant_id": tenant.id}


@router.post("/login")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)
):
    # 1. Fetch user asynchronously
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    # 2. Verify credentials
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    # 3. Generate JWT (This function remains exactly as you wrote it in Step 3)
    access_token = create_access_token(
        data={"sub": user.email, "tenant_id": user.tenant_id},
        expires_delta=timedelta(minutes=30),
    )

    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/refresh")
async def refresh_token(refresh_token: str = Header(..., alias="Authorization")):
    # In a real app, expect "Bearer <token>" and parse it
    token = refresh_token.split(" ")[1] if " " in refresh_token else refresh_token
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")

        email: str = payload.get("sub")
        tenant_id: str = payload.get("tenant_id")
        if email is None or tenant_id is None:
            raise HTTPException(status_code=401, detail="Invalid token payload")

        # Generate new access token
        new_access_token = create_access_token(
            data={"sub": email, "tenant_id": tenant_id},
            expires_delta=timedelta(minutes=30),
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid refresh token")
