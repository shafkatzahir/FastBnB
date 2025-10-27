import json
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from redis import Redis
from typing import List

from .. import schemas, crud, auth, models
from ..database import get_db, get_redis_client

router = APIRouter(prefix="/properties", tags=["Properties"])


@router.post("/", response_model=schemas.PropertyRead, status_code=status.HTTP_201_CREATED)
def create_property(
        property: schemas.PropertyCreate,
        db: Session = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        current_user: models.User = Depends(auth.get_current_admin_user)
):
    # When a new property is added, invalidate the cache.
    redis_client.delete("all_properties")
    return crud.create_property(db=db, property=property, owner_id=current_user.id)


@router.get("/", response_model=List[schemas.PropertyRead])
def read_properties(
        skip: int = 0,
        limit: int = 100,
        db: Session = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client)
):
    # 1. Check cache first
    cached_properties = redis_client.get("all_properties")
    if cached_properties:
        return json.loads(cached_properties)

    # 2. If cache miss, query DB
    properties = crud.get_properties(db, skip=skip, limit=limit)

    # Manually serialize to handle datetime objects
    properties_list = [schemas.PropertyRead.from_orm(p).model_dump() for p in properties]

    # 3. Store result in cache with an expiration time (e.g., 5 minutes)
    redis_client.set("all_properties", json.dumps(properties_list, default=str), ex=300)

    return properties_list


@router.get("/{property_id}", response_model=schemas.PropertyRead)
def read_property(
        property_id: int,
        db: Session = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client)
):
    cache_key = f"property_{property_id}"
    cached_property = redis_client.get(cache_key)
    if cached_property:
        return json.loads(cached_property)

    db_property = crud.get_property(db, property_id=property_id)
    if db_property is None:
        raise HTTPException(status_code=404, detail="Property not found")

    property_data = schemas.PropertyRead.from_orm(db_property).model_dump()
    redis_client.set(cache_key, json.dumps(property_data, default=str), ex=300)
    return property_data


@router.delete("/{property_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_property(
        property_id: int,
        db: Session = Depends(get_db),
        redis_client: Redis = Depends(get_redis_client),
        current_user: models.User = Depends(auth.get_current_admin_user)
):
    if not crud.delete_property(db=db, property_id=property_id):
        raise HTTPException(status_code=404, detail="Property not found")

    # Invalidate caches
    redis_client.delete(f"property_{property_id}")
    redis_client.delete("all_properties")
    return {"detail": "Property deleted successfully"}