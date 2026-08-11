from app.api.auth import get_current_tenant
from fastapi import APIRouter, Depends

router = APIRouter(prefix="/v1", tags=["tenant-test"])


@router.get("/me")
async def get_tenant_info(tenant_id: str = Depends(get_current_tenant)):
    # Any route using Depends(get_current_tenant) will strictly require a valid JWT
    # and automatically extract the isolated tenant ID for downstream database/MinIO queries.
    return {"message": "You have securely accessed the API.", "tenant_id": tenant_id}
