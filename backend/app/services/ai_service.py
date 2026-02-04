"""
AI服务 - 统一的AI调用接口
支持DeepSeek API
"""

from openai import OpenAI
from typing import Optional


class AIService:
    """AI服务 - 统一的AI调用接口"""
    
    def __init__(self):
        """初始化AI服务"""
        # DeepSeek API配置
        self.api_key = "sk-11fe906e92c84e0f95c9f04ae6ed1565"
        self.base_url = "https://api.deepseek.com/v1"
        self.model_name = "deepseek-chat"
        
        # 初始化OpenAI客户端（兼容DeepSeek）
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
    
    async def generate_content(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        生成AI内容
        
        Args:
            prompt: 提示文本
            temperature: 温度参数（0-1）
            max_tokens: 最大token数
            
        Returns:
            AI生成的文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"调用DeepSeek API失败: {str(e)}")
    
    async def chat(
        self,
        messages: list,
        temperature: float = 0.7,
        max_tokens: int = 4000
    ) -> str:
        """
        对话模式
        
        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数（0-1）
            max_tokens: 最大token数
            
        Returns:
            AI生成的文本
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            raise Exception(f"调用DeepSeek API失败: {str(e)}")


# 创建全局实例
ai_service = AIService()
