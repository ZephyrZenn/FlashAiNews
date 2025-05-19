import { Settings } from "../types";
import axios from "../utils/axios";
import { transformResponse } from "../utils/transform-response";

export const getSetting = async () => {
    const resp = await axios.get("/setting");
    const data = transformResponse(resp);
    return data;
}

export const updateSetting = async (setting: Settings) => {
    const resp = await axios.post("/setting", setting);
    const data = transformResponse(resp);
    return data;
}