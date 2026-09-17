from fastapi import APIRouter
from app.api.v1.endpoints import health, auth, admin, organization, cases, activities, attachments, ai, sla, escalations

api_v1_router = APIRouter()

# Register endpoint groups
api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(organization.router, prefix="/organization", tags=["Organization"])
api_v1_router.include_router(admin.router, prefix="/admin", tags=["Administration"])
api_v1_router.include_router(cases.router, prefix="/cases", tags=["Cases"])
api_v1_router.include_router(activities.router, prefix="/cases", tags=["Case Activities"])
api_v1_router.include_router(attachments.router, prefix="/cases", tags=["Case Attachments"])
api_v1_router.include_router(ai.router, prefix="/cases", tags=["AI Copilot & Insights"])
api_v1_router.include_router(sla.router, tags=["SLA & Risk"])
api_v1_router.include_router(escalations.router, tags=["Escalations & Automation"])

