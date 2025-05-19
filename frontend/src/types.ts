interface CommonResult<T> {
  success: boolean;
  message: string;
  data: T;
}

interface FeedBrief {
  id: number;
  title: string;
  content: string;
  pubDate: Date;
  groupId: number;
  group?: FeedGroup;
}

interface FeedGroup {
  id: number;
  title: string;
  desc: string;
  feeds: Feed[];
}

interface Feed {
  id: number;
  title: string;
  url: string;
  desc: string;
}

export enum LLMProvider {
  OPENAI = "openai",
  GEMINI = "gemini",
  DEEPSEEK = "deepseek",
}

interface ModelConfig {
  name: string;
  model: string;
  provider: LLMProvider;
  apiKey: string;
  baseUrl: string;
  isDefault: boolean;
}

interface Settings {
  prompt: string;
  model: ModelConfig;
}

export type { CommonResult, Feed, FeedBrief, FeedGroup, ModelConfig, Settings };
