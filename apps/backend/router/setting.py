from fastapi import APIRouter

from apps.backend.models.common import success_with_data
from apps.backend.models.request import ModifySettingRequest
from apps.backend.models.view_model import ModelSettingVO, SettingResponse, SettingVO
from apps.backend.services import setting_service

router = APIRouter(prefix="/setting", tags=["setting"])


@router.get("/", response_model=SettingResponse)
async def get_setting():
    setting = setting_service.get_setting()
    model = setting.model
    return success_with_data(
        SettingVO(
            model=ModelSettingVO(
                model=model.model,
                provider=model.provider.value,
                api_key="********",
                base_url=model.base_url or "",
            ),
        )
    )


@router.post("/")
async def modify_setting(request: ModifySettingRequest):
    setting_service.update_setting(request.model)
    return success_with_data(None)
