-- 添加 summary 和 ext_info 列到 feed_brief 表
ALTER TABLE feed_brief
ADD COLUMN IF NOT EXISTS summary TEXT DEFAULT '',
ADD COLUMN IF NOT EXISTS ext_info JSONB DEFAULT '[]'::jsonb;

-- 添加注释
COMMENT ON COLUMN feed_brief.summary IS '简报概要，提取自内容中的所有二级标题';
COMMENT ON COLUMN feed_brief.ext_info IS '使用的外部搜索结果，JSON格式存储';
