import axios from "axios";
import { BASE_URL } from "../constants";
import { Feed, FeedBrief, FeedGroup } from "../types";
import { transformResponse } from "../utils/transform-response";
import { ModifyFeedGroupRequest } from "./request";

export const getFeedBrief = async (
  briefId: number | undefined
): Promise<FeedBrief> => {
  const url = briefId ? `${BASE_URL}/brief/${briefId}` : `${BASE_URL}/`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};

export const getFeedGroups = async (): Promise<FeedGroup[]> => {
  const url = `${BASE_URL}/groups`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};

export const getFeedGroupDetail = async (id: number): Promise<FeedGroup> => {
  const url = `${BASE_URL}/groups/${id}`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};

export const getAllFeeds = async (): Promise<Feed[]> => {
  const url = `${BASE_URL}/feeds`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};

export const createFeedGroup = async (group: FeedGroup): Promise<FeedGroup> => {
  const url = `${BASE_URL}/groups`;
  const request: ModifyFeedGroupRequest = {
    title: group.title,
    desc: group.desc,
    feedIds: group.feeds.map((feed) => feed.id),
  };
  const resp = await axios.post(url, request);
  const data = transformResponse(resp);
  return data;
};

export const updateFeedGroup = async (group: FeedGroup): Promise<FeedGroup> => {
  const url = `${BASE_URL}/groups/${group.id}`;
  const request: ModifyFeedGroupRequest = {
    title: group.title,
    desc: group.desc,
    feedIds: group.feeds.map((feed) => feed.id),
  };
  const resp = await axios.put(url, request);
  const data = transformResponse(resp);
  return data;
};
