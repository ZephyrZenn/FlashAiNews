import axios from "axios";
import { BASE_URL } from "../constants";
import { FeedBrief } from "../types";
import { transformResponse } from "../utils/transform-response";

export const getFeedBrief = async (briefId: number | undefined): Promise<FeedBrief> => {
  const url = briefId ? `${BASE_URL}/brief/${briefId}` : `${BASE_URL}/`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};
