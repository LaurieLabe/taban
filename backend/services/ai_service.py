import os
import json
import re
import requests

DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "")
DEEPSEEK_BASE_URL = "https://api.deepseek.com"

SYSTEM_PROMPT = """你叫小伴，是她伴的女性AI搭子助手。你的任务是：

1. 以"第一个搭子/朋友"的口吻和用户进行自然轻松的对话
2. 对话风格：温暖、好奇、不评判，像新认识的朋友在聊天
3. 通过对话推断用户的隐性特质

你需要评估的5个隐性维度（0-100分，50为中性基准）：
- empathy（情感共鸣度）：越高越容易共情他人，越低越偏理性分析
- agency（主体性）：越高越主动发起、有主见，越低越随性、喜欢跟随
- energy（社交能量）：越高越外向、喜欢社交，越低越需要独处空间
- sensitivity（敏感度）：越高越敏感细腻，越低越钝感、大条
- openness（开放度）：越高越喜欢探索新体验，越低越偏好安稳熟悉

回复格式：先自然语言回复，然后在最后一行附上 JSON 格式的隐性特质评估，格式如下：
{"empathy": 65, "agency": 50, "energy": 45, "sensitivity": 70, "openness": 55}

这是第1轮对话，请用轻松的语气先自我介绍，然后引导用户聊聊自己。"""


def chat_with_ai(user_message: str) -> dict | None:
    """调用 DeepSeek V4 Pro API，返回 AI 回复和隐性量表"""
    if not DEEPSEEK_API_KEY:
        return _fallback()

    try:
        resp = requests.post(
            f"{DEEPSEEK_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-v4-pro",
                "messages": [
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message}
                ],
                "temperature": 0.8,
                "max_tokens": 2000
            },
            timeout=30
        )

        if resp.status_code != 200:
            print(f"DeepSeek API 返回 {resp.status_code}: {resp.text[:200]}")
            return _fallback()

        data = resp.json()
        content = data["choices"][0]["message"]["content"]

        # 提取 JSON 和文本
        reply, traits = _parse_response(content)
        return {"reply": reply, "traits": traits}

    except Exception as e:
        print(f"DeepSeek API 调用失败: {e}")
        return _fallback()


def _parse_response(content: str) -> tuple[str, dict]:
    """从 AI 回复中分离文本和 JSON"""
    # 尝试提取最后一个 JSON 对象
    json_match = re.search(r'\{[^{}]*"empathy"[^{}]*\}', content)
    if json_match:
        try:
            traits = json.loads(json_match.group())
            reply = content[:json_match.start()].strip()
            return reply, traits
        except json.JSONDecodeError:
            pass

    # 没有 JSON 则返回默认值
    return content, {"empathy": 60, "agency": 55, "energy": 50, "sensitivity": 60, "openness": 55}


def _fallback() -> dict:
    return {
        "reply": "收到你的消息了～我能感受到你是一个真诚的人，想多了解你一点，你平时最喜欢做什么呢？",
        "traits": {"empathy": 60, "agency": 55, "energy": 50, "sensitivity": 60, "openness": 55}
    }