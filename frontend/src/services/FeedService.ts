import { BASE_URL } from "../constants";
import { Feed, FeedBrief, FeedGroup } from "../types";
import axios from "../utils/axios";
import { transformResponse } from "../utils/transform-response";
import { ModifyFeedGroupRequest } from "./request";

export const getHomeFeeds = async (): Promise<FeedBrief> => {
  const url = `${BASE_URL}/`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};

export const getFeedBrief = async (
  briefId: number,
  time?: Date
): Promise<FeedBrief> => {
  let url = "";
  let params = {};
  if (time === undefined) {
    url = `${BASE_URL}/briefs/${briefId}/today`;
  } else {
    url = `${BASE_URL}/briefs/${briefId}`;
    params = {
      time: time,
    };
  }
  const resp = await axios.get(url, { params });
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

export const getHistoryBriefs = async (
  groupId: number
): Promise<FeedBrief[]> => {
  const url = `${BASE_URL}/briefs/${groupId}/history`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};

export const getDefaultBriefHistory = async (): Promise<FeedBrief[]> => {
  const url = `${BASE_URL}/briefs/default`;
  const resp = await axios.get(url);
  const data = transformResponse(resp);
  return data;
};
