import { Feed, FeedBrief, FeedGroup } from "../types";
import axios from "../utils/axios";
import { transformResponse } from "../utils/transform-response";
import {
  ImportOpmlRequest,
  ModifyFeedGroupRequest,
  ModifyFeedRequest,
} from "./request";

export const getHomeFeeds = async (): Promise<FeedBrief> => {
  const resp = await axios.get("/");
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
    url = `/briefs/${briefId}/today`;
  } else {
    url = `/briefs/${briefId}`;
    params = {
      time: time,
    };
  }
  const resp = await axios.get(url, { params });
  const data = transformResponse(resp);
  return data;
};

export const getFeedGroups = async (): Promise<FeedGroup[]> => {
  const resp = await axios.get("/groups");
  const data = transformResponse(resp);
  return data;
};

export const getFeedGroupDetail = async (id: number): Promise<FeedGroup> => {
  const resp = await axios.get(`/groups/${id}`);
  const data = transformResponse(resp);
  return data;
};

export const getAllFeeds = async (): Promise<Feed[]> => {
  const resp = await axios.get("/feeds");
  const data = transformResponse(resp);
  return data;
};

export const createFeedGroup = async (group: FeedGroup): Promise<FeedGroup> => {
  const request: ModifyFeedGroupRequest = {
    title: group.title,
    desc: group.desc,
    feedIds: group.feeds.map((feed) => feed.id),
  };
  const resp = await axios.post("/groups", request);
  const data = transformResponse(resp);
  return data;
};

export const updateFeedGroup = async (group: FeedGroup): Promise<FeedGroup> => {
  const request: ModifyFeedGroupRequest = {
    title: group.title,
    desc: group.desc,
    feedIds: group.feeds.map((feed) => feed.id),
  };
  const resp = await axios.put(`/groups/${group.id}`, request);
  const data = transformResponse(resp);
  return data;
};

export const getHistoryBriefs = async (
  groupId: number
): Promise<FeedBrief[]> => {
  const resp = await axios.get(`/briefs/${groupId}/history`);
  const data = transformResponse(resp);
  return data;
};

export const getDefaultBriefHistory = async (): Promise<FeedBrief[]> => {
  const resp = await axios.get("/briefs/default");
  const data = transformResponse(resp);
  return data;
};

export const importOpml = async (
  fileUrl?: string,
  fileContent?: string
): Promise<void> => {
  const request: ImportOpmlRequest = {
    url: fileUrl,
    content: fileContent,
  };
  const resp = await axios.post("/feeds/import", request);
  const data = transformResponse(resp);
  return data;
};

export const createFeed = async (request: ModifyFeedRequest) => {
  const resp = await axios.post("/feeds", request);
  const data = transformResponse(resp);
  return data;
};

export const updateFeed = async (id: number, request: ModifyFeedRequest) => {
  const resp = await axios.put(`/feeds/${id}`, request);
  const data = transformResponse(resp);
  return data;
};

export const deleteFeed = async (id: number) => {
  const resp = await axios.delete(`/feeds/${id}`);
  const data = transformResponse(resp);
  return data;
};
