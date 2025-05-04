/* eslint-disable @typescript-eslint/no-explicit-any */
import axios, { AxiosResponse } from "axios";
import { CommonResult } from "../types";

export const transformResponse = <T = any>(
  response: AxiosResponse<CommonResult<T>>
): T => {
  if (response.status >= 200 && response.status < 300) {
    const res = response.data;
    const err = response as unknown as Error;
    if (res?.success) {
      return parseDateFields(res.data, ["pubDate"]);
    }
    throw new Error(res.message || err.message || "Unknown Error");
  } else {
    throw new Error(`${response.status}: ${response.statusText}`);
  }
};

const parseDateFields = (obj: any, fields: [string]) => {
  if (obj === null || obj === undefined) {
    return {};
  }
  fields.forEach((field) => {
    if (obj[field]) {
      const date = new Date(obj[field]);
      if (!isNaN(date.getTime())) {
        obj[field] = date;
      }
    }
  });
  return obj;
};

export const formatErrorMessage = (e: Error) => {
  if (axios.isAxiosError(e)) {
    return `${e.response?.status}: ${e.response?.statusText}`;
  }
  return e.message;
};
