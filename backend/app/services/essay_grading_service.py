"""
问答题AI智能打分服务
基于AI对学生的问答题进行智能评分
"""

import json
import os
from typing import Dict, Any, Optional
from pathlib import Path

from app.services.ai_service import ai_service


class EssayGradingService:
    """问答题AI打分服务"""
    
    def __init__(self):
        self.ai_service = ai_service
        self.skill_file = Path(__file__).parent.parent / "skills" / "essay_grading.md"
    
    async def grade_essay(
        self,
        question_text: str,
        question_type: str,
        reference_answer: str,
        student_answer: str,
        max_score: float = 100,
        grading_criteria: Optional[Dict[str, Any]] = None,
        min_word_count: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        对问答题进行AI打分
        
        Args:
            question_text: 题目文本
            question_type: 题目类型 (essay/text)
            reference_answer: 参考答案
            grading_criteria: 评分标准
            min_word_count: 最小字数要求
            student_answer: 学生答案
            max_score: 题目满分
            
        Returns:
            打分结果，包含分数、评语等
        """
        print(f"📝 开始AI打分")
        print(f"题目: {question_text[:50]}...")
        print(f"学生答案: {student_answer[:100]}...")
        print(f"满分: {max_score}")
        
        # 读取skill文件
        skill_content = self._load_skill_file()
        
        # 构建打分prompt
        prompt = self._build_grading_prompt(
            question_text=question_text,
            question_type=question_type,
            reference_answer=reference_answer,
            grading_criteria=grading_criteria,
            min_word_count=min_word_count,
            student_answer=student_answer,
            max_score=max_score,
            skill_content=skill_content
        )
        
        # 调用AI进行打分
        try:
            result = await self.ai_service.generate_content(prompt)
            
            # 解析AI返回的JSON
            grading_result = self._parse_grading_result(result)
            
            print(f"✅ AI打分完成: 得分={grading_result.get('score')}, 等级={grading_result.get('level')}")
            
            return grading_result
            
        except Exception as e:
            print(f"❌ AI打分失败: {e}")
            # 返回默认评分
            return self._get_default_grading(student_answer, max_score)
    
    def _load_skill_file(self) -> str:
        """加载skill文件内容"""
        try:
            with open(self.skill_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"⚠️ 加载skill文件失败: {e}")
            return ""
    
    def _build_grading_prompt(
        self,
        question_text: str,
        question_type: str,
        reference_answer: str,
        grading_criteria: Optional[Dict[str, Any]],
        min_word_count: Optional[int],
        student_answer: str,
        max_score: float,
        skill_content: str
    ) -> str:
        """构建打分prompt"""
        
        prompt = f"""你是一个专业的教育评分专家，请根据以下要求对学生的问答题进行打分。

## 题目信息
- 题目类型: {question_type}
- 题目内容: {question_text}
- 题目满分: {max_score}分
"""
        
        if reference_answer:
            prompt += f"- 参考答案: {reference_answer}\n"
        
        if grading_criteria:
            prompt += f"- 评分标准: {json.dumps(grading_criteria, ensure_ascii=False)}\n"
        
        if min_word_count:
            prompt += f"- 最小字数要求: {min_word_count}字\n"
        
        prompt += f"""
## 学生答案
{student_answer}

## 打分要求
"""
        
        if skill_content:
            prompt += f"""
请严格按照以下skill文件中的打分原则和标准进行评分：

{skill_content}
"""
        else:
            prompt += """
请按照以下原则进行打分：
1. 严中有爱：坚持评分标准，但也要发现学生的闪光点
2. 理中有情：评分有理有据，评语要体现人文关怀
3. 具体反馈：指出答得好的地方和需要改进的地方
4. 鼓励进步：评语要传递正能量

评分标准：
- 内容完整性（40%）：是否覆盖了所有关键要点
- 准确性（35%）：核心概念是否正确
- 深度（20%）：理解是否深入，是否有独到见解
- 表达（5%）：语言表达是否清晰，逻辑是否合理
"""
        
        prompt += """
## 输出要求
必须严格按照以下JSON格式输出，不要有任何其他文字：

```json
{
  "score": 分数,
  "max_score": 满分,
  "percentage": 百分比,
  "level": "等级(满分/优秀/良好/及格/不及格)",
  "score_breakdown": {
    "content_completeness": 内容完整性得分,
    "accuracy": 准确性得分,
    "depth": 深度得分,
    "expression": 表达得分
  },
  "strengths": ["优点1", "优点2", "优点3"],
  "areas_for_improvement": ["改进建议1", "改进建议2"],
  "comment": "综合评语",
  "detailed_feedback": [
    {
      "point": "要点名称",
      "score": 得分,
      "max_score": 满分,
      "feedback": "具体反馈"
    }
  ]
}
```

注意事项：
1. score必须是数字，不能超过max_score
2. percentage = (score / max_score) * 100
3. level根据percentage确定：90%以上=满分，80-89%=优秀，70-79%=良好，60-69%=及格，60%以下=不及格
4. strengths至少要有2-3个优点
5. areas_for_improvement至少要有1-2个改进建议
6. comment要体现人文关怀，既指出优点，也给出建议，传递正能量
7. detailed_feedback要具体，针对每个要点给出反馈
8. 只输出JSON，不要有任何markdown标记或其他文字
"""
        
        return prompt
    
    def _parse_grading_result(self, result: str) -> Dict[str, Any]:
        """解析AI返回的打分结果"""
        try:
            # 尝试直接解析JSON
            return json.loads(result)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取JSON部分
            import re
            json_match = re.search(r'```json\s*(.*?)\s*```', result, re.DOTALL)
            if json_match:
                try:
                    return json.loads(json_match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # 如果还是失败，尝试提取花括号内容
            brace_match = re.search(r'\{.*\}', result, re.DOTALL)
            if brace_match:
                try:
                    return json.loads(brace_match.group(0))
                except json.JSONDecodeError:
                    pass
            
            # 如果都失败，返回默认评分
            print(f"⚠️ 解析AI返回结果失败，使用默认评分")
            return self._get_default_grading("", 100)
    
    def _get_default_grading(self, student_answer: str, max_score: float) -> Dict[str, Any]:
        """获取默认评分（当AI打分失败时）"""
        
        # 根据答案长度给一个基础分
        answer_length = len(student_answer.strip())
        
        if answer_length == 0:
            score = 0
            level = "不及格"
        elif answer_length < 50:
            score = max_score * 0.4
            level = "不及格"
        elif answer_length < 100:
            score = max_score * 0.6
            level = "及格"
        elif answer_length < 200:
            score = max_score * 0.75
            level = "良好"
        else:
            score = max_score * 0.85
            level = "优秀"
        
        percentage = (score / max_score) * 100 if max_score > 0 else 0
        
        return {
            "score": round(score, 1),
            "max_score": max_score,
            "percentage": round(percentage, 1),
            "level": level,
            "score_breakdown": {
                "content_completeness": round(score * 0.4, 1),
                "accuracy": round(score * 0.35, 1),
                "depth": round(score * 0.2, 1),
                "expression": round(score * 0.05, 1)
            },
            "strengths": [
                "完成了作答",
                "有一定的思考"
            ],
            "areas_for_improvement": [
                "建议更深入地理解题目",
                "可以尝试更详细地阐述观点"
            ],
            "comment": "感谢你的作答。建议你多复习相关知识，加强对概念的理解。相信通过努力，你会有更大的进步！",
            "detailed_feedback": [
                {
                    "point": "内容完整性",
                    "score": round(score * 0.4, 1),
                    "max_score": round(max_score * 0.4, 1),
                    "feedback": "基于答案长度的基础评分"
                }
            ]
        }


# 创建全局实例
essay_grading_service = EssayGradingService()
