-- 为 questions 表添加缺失的字段
-- 用于支持问答题的参考材料、字数限制和评分标准

ALTER TABLE questions ADD COLUMN IF NOT EXISTS reference_files JSONB;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS min_word_count INTEGER;
ALTER TABLE questions ADD COLUMN IF NOT EXISTS grading_criteria JSONB;

COMMENT ON COLUMN questions.reference_files IS '问答题参考材料文件URL列表';
COMMENT ON COLUMN questions.min_word_count IS '问答题最小作答字数';
COMMENT ON COLUMN questions.grading_criteria IS '问答题评分标准';
