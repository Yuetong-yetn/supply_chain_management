# add-api — Add a new API endpoint

Adding a new API route module to the FastAPI backend.

## Checklist

### 1. Create the router file
Place in `backend/app/api/routers/your_feature.py`:

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db
from app.core.response import success_response

router = APIRouter(prefix="/api/your-feature", tags=["Your Feature"])

@router.get("")
def list_items(db: Session = Depends(get_db)):
    # ... logic (delegate to service layer)
    return success_response({"items": result})
```

### 2. Register the router
In `backend/app/main.py`, add the import and include_router line:

```python
from app.api.routers import your_feature
# ...
app.include_router(your_feature.router)
```

### 3. Create service (business logic)
Place in `backend/app/services/your_service.py`

### 4. Create schema (Pydantic models)
Place in `backend/app/schemas/your_feature.py`

### 5. Create model (if new table)
Place in `backend/app/models/your_model.py`

## API conventions
- **All responses**: `{"success": bool, "message": str, "data": any}` via `success_response()` / `error_response()`
- **Pagination**: use `page_response(items, total, page, page_size)`
- **Errors**: raise `BusinessException("message")` for 400s, let FastAPI handle 422 validation errors
- **Database**: use `Depends(get_db)` for session injection
- **Prefix**: always `/api/` prefix on routes
- **Tags**: use Chinese tags matching the domain

## Testing
Create `backend/tests/test_your_feature.py` using `TestClient`:
```python
def test_list_items(api_client):
    response = api_client.get("/api/your-feature")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
```
