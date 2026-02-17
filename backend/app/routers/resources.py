"""Resource CRUD endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models.resource import Resource
from app.models.user import User
from app.schemas.resource import (
    VALID_CATEGORIES,
    VALID_CONDITIONS,
    ResourceCreate,
    ResourceList,
    ResourceOut,
    ResourceUpdate,
)

router = APIRouter(prefix="/resources", tags=["resources"])


@router.get("", response_model=ResourceList)
def list_resources(
    category: str | None = Query(None),
    available: bool | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """List resources with optional filters."""
    q = db.query(Resource).options(joinedload(Resource.owner))
    if category:
        q = q.filter(Resource.category == category)
    if available is not None:
        q = q.filter(Resource.is_available == available)
    total = q.count()
    items = q.order_by(Resource.created_at.desc()).offset(skip).limit(limit).all()
    return ResourceList(items=items, total=total)


@router.post("", response_model=ResourceOut, status_code=status.HTTP_201_CREATED)
def create_resource(
    body: ResourceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create a new resource listing."""
    if body.category not in VALID_CATEGORIES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
        )
    if body.condition and body.condition not in VALID_CONDITIONS:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid condition. Must be one of: {VALID_CONDITIONS}",
        )

    resource = Resource(
        title=body.title,
        description=body.description,
        category=body.category,
        condition=body.condition,
        owner_id=current_user.id,
    )
    db.add(resource)
    db.commit()
    db.refresh(resource)
    # Eager-load owner for response serialisation
    _ = resource.owner
    return resource


@router.get("/{resource_id}", response_model=ResourceOut)
def get_resource(resource_id: int, db: Session = Depends(get_db)):
    """Get a single resource by ID."""
    resource = (
        db.query(Resource)
        .options(joinedload(Resource.owner))
        .filter(Resource.id == resource_id)
        .first()
    )
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    return resource


@router.patch("/{resource_id}", response_model=ResourceOut)
def update_resource(
    resource_id: int,
    body: ResourceUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update a resource (owner only)."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    if resource.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your resource")

    if body.title is not None:
        resource.title = body.title
    if body.description is not None:
        resource.description = body.description
    if body.category is not None:
        if body.category not in VALID_CATEGORIES:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid category. Must be one of: {VALID_CATEGORIES}",
            )
        resource.category = body.category
    if body.condition is not None:
        if body.condition not in VALID_CONDITIONS:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid condition. Must be one of: {VALID_CONDITIONS}",
            )
        resource.condition = body.condition
    if body.is_available is not None:
        resource.is_available = body.is_available

    db.commit()
    db.refresh(resource)
    _ = resource.owner
    return resource


@router.delete("/{resource_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_resource(
    resource_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete a resource (owner only)."""
    resource = db.query(Resource).filter(Resource.id == resource_id).first()
    if not resource:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")
    if resource.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your resource")
    db.delete(resource)
    db.commit()
