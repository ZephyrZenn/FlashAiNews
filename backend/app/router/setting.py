from fastapi import APIRouter

from app.models.common import success_with_data
from app.models.request import ModifySettingRequest, UpdateBriefTimeRequest
from app.models.view_model import ModelSettingVO, SettingResponse, SettingVO
from app.services import setting_service

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
            prompt=setting.prompt,
            brief_time=setting.brief_time.strftime("%H:%M"),
        )
    )


@router.post("/")
async def modify_setting(request: ModifySettingRequest):
    setting_service.update_setting(request.prompt, request.model, request.brief_time)
    return success_with_data(None)


@router.post("/brief-time")
async def set_brief_time(request: UpdateBriefTimeRequest):
    setting_service.update_setting(None, None, request.brief_time)
    return success_with_data(None)
