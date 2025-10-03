from fastapi import APIRouter

from app.models.common import success_with_data
from app.models.request import ModifySettingRequest
from app.models.view_model import SettingResponse
from app.services import setting_service

router = APIRouter(prefix="/setting", tags=["setting"])


@router.get("/", response_model=SettingResponse)
async def get_setting():
    setting = setting_service.get_setting()
    setting.model.api_key = "********"
    return success_with_data(setting)


@router.post("/")
async def modify_setting(request: ModifySettingRequest):
    setting_service.update_setting(request.prompt, request.model)
    return success_with_data(None)
