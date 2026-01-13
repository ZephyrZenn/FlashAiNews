from fastapi import APIRouter

from apps.backend.models.common import success_with_data
from apps.backend.models.converters import request_to_model_config
from apps.backend.models.request import ModifySettingRequest
from apps.backend.models.view_model import SettingResponse
from apps.backend.services import setting_service

router = APIRouter(prefix="/setting", tags=["setting"])


@router.get("/", response_model=SettingResponse)
async def get_setting():
    setting_vo = setting_service.get_setting()
    return success_with_data(setting_vo)


@router.post("/")
async def modify_setting(request: ModifySettingRequest):
    model_config = request_to_model_config(request.model) if request.model else None
    setting_service.update_setting(model_config)
    return success_with_data(None)
