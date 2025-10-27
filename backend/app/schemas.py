# import datetime
#
# from pydantic import BaseModel, Field
# from typing import Optional
# from enum import Enum as PyEnum
#
#
# # Use the same Python Enum for Pydantic validation
# class UserRole(str, PyEnum):
#     USER = "user"
#     ADMIN = "admin"
#
#
# # --- USER SCHEMAS ---
#
# class UserBase(BaseModel):
#     username: str = Field(..., max_length=50)
#     role: UserRole = UserRole.USER  # Default to 'user'
#
#
# class UserCreate(UserBase):
#     password: str = Field(..., min_length=8)
#
#
# class UserRead(UserBase):
#     id: int
#
#     # We never expose the password hash or refresh token hash
#     class Config:
#         from_attributes = True
#
#
# class Token(BaseModel):
#     access_token: str
#     token_type: str = "bearer"
#
#
# class TokenPayload(BaseModel):
#     sub: Optional[int] = None  # Subject will be the user ID
#     role: Optional[UserRole] = None
#
#
# # --- PROPERTY SCHEMAS ---
#
# class PropertyBase(BaseModel):
#     location: str
#     description: str
#     size_sqft: int = Field(..., gt=0)
#     price_per_night: float = Field(..., gt=0)
#
#
# class PropertyCreate(PropertyBase):
#     # Owner ID will be taken from the logged-in admin user
#     pass
#
#
# class PropertyRead(PropertyBase):
#     id: int
#     owner_id: int
#     created_at: datetime.datetime  # Use str for simple display of timestamp
#
#     class Config:
#         from_attributes = True

from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum as PyEnum
import datetime

# +++ NEW: Import the status Enum from the models +++
from .models import PropertyStatus

# Use the same Python Enum for Pydantic validation
class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"

# --- USER SCHEMAS ---
class UserBase(BaseModel):
    username: str = Field(..., max_length=50)
    role: UserRole = UserRole.USER

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserRead(UserBase):
    id: int
    class Config:
        from_attributes = True

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenPayload(BaseModel):
    sub: Optional[int] = None
    role: Optional[UserRole] = None

# --- PROPERTY SCHEMAS ---
class PropertyBase(BaseModel):
    location: str
    description: str
    size_sqft: int = Field(..., gt=0)
    price_per_night: float = Field(..., gt=0)

class PropertyCreate(PropertyBase):
    pass

class PropertyRead(PropertyBase):
    id: int
    owner_id: int
    created_at: datetime.datetime
    # +++ NEW: Add status to the response model +++
    status: PropertyStatus

    class Config:
        from_attributes = True

