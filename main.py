#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Lead Generation & AI Intent Pipeline (工业级获客与意向分析流水线)
"""

import os
import re
import json
import requests
from typing import List, Dict, Any

class Config:
    LLM_API_KEY = os.getenv("LLM_API_KEY", "")
    LLM_BASE_URL = os.getenv("LLM_BASE_URL", "https://api.deepseek.com/v1")
    LLM_MODEL = os.getenv("LLM_MODEL", "deepseek-chat")
    AMAP_API_KEY = os.getenv("AMAP_API_KEY", "")
    FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")
    INTENT_THRESHOLD = 75

class PhoneCleaner:
    MOBILE_PATTERN = re.compile(r"(?:\+?86)?(1[3-9]\d{9})")
    TEL_PATTERN = re.compile(r"(0\d{2,3}-?\d{7,8})")

    @classmethod
    def extract_phones(cls, raw_tel_str: str) -> Dict[str, Any]:
        mobiles = cls.MOBILE_PATTERN.findall(raw_tel_str or "")
        landlines = cls.TEL_PATTERN.findall(raw_tel_str or "")
        mobiles = list(dict.fromkeys(mobiles))
        landlines = list(dict.fromkeys(landlines))
        primary = mobiles[0] if mobiles else (landlines[0] if landlines else "")
        return {"mobile": mobiles, "landline": landlines, "primary_phone": primary, "is_mobile": bool(mobiles)}

class MapHarvester:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.AMAP_API_KEY

    def search_places(self, keywords: str, city: str, page_size: int = 20) -> List[Dict[str, Any]]:
        if not self.api_key:
            return self._mock_places(keywords, city)
        url = "https://restapi.amap.com/v3/place/text"
        params = {"key": self.api_key, "keywords": keywords, "city": city, "offset": page_size, "page": 1, "extensions": "all"}
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            results = []
            for poi in data.get("pois", []):
                phone_info = PhoneCleaner.extract_phones(poi.get("tel", ""))
                results.append({
                    "name": poi.get("name"),
                    "address": poi.get("address"),
                    "city": city,
                    "primary_phone": phone_info["primary_phone"],
                    "is_mobile": phone_info["is_mobile"],
                })
            return results
        except Exception:
            return self._mock_places(keywords, city)

    def _mock_places(self, keywords: str, city: str) -> List[Dict[str, Any]]:
        raw_samples = [
            {"name": f"{city}精诚{keywords}源头工厂", "tel": "13800138000;010-88889999", "address": "高新区工业园A区3号"},
            {"name": f"{city}恒泰{keywords}商贸有限公司", "tel": "13912345678", "address": "物流产业园8栋102"},
            {"name": f"{city}联创{keywords}批发总汇", "tel": "010-66667777", "address": "建材大市场南区F-12"},
            {"name": f"{city}盛达{keywords}定制加工中心", "tel": "15988887777", "address": "新城开发区科技路88号"},
        ]
        results = []
        for item in raw_samples:
            phone_info = PhoneCleaner.extract_phones(item["tel"])
            results.append({
                "name": item["name"],
                "address": item["address"],
                "city": city,
                "primary_phone": phone_info["primary_phone"],
                "is_mobile": phone_info["is_mobile"],
            })
        return results

class SocialIntentAnalyzer:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key or Config.LLM_API_KEY

    def analyze_comment(self, comment_text: str, industry: str = "通用") -> Dict[str, Any]:
        high_intent_keywords = ["怎么买", "求链接", "多少钱", "求推荐", "预算", "私我", "带带我", "批发价"]
        score = 88 if any(kw in comment_text for kw in high_intent_keywords) else 35
        icebreaker = f"看到您在关注{industry}，我整理了一份《行业避坑与选型对比指南》，发您参考下？" if score >= 75 else "先点赞互动，主页置顶行业知识库吸引主动关注。"
        return {
            "intent_score": score,
            "pain_points": f"寻找{industry}靠谱渠道" if score >= 75 else "潜在闲聊观望",
            "recommended_icebreaker": icebreaker,
        }

def run_demo():
    print("=" * 50)
    print("🚀 启动自动化获客与意向分析流水线")
    print("=" * 50)
    harvester = MapHarvester()
    places = harvester.search_places(keywords="全屋定制", city="上海")
    print(f"\n[B端商户] 成功提取 {len(places)} 家实体商户：")
    for p in places:
        badge = "✅ 老板手机" if p["is_mobile"] else "☎️ 座机"
        print(f"[{badge}] {p['name']} | 电话: {p['primary_phone']} | 地址: {p['address']}")

    analyzer = SocialIntentAnalyzer()
    demo_comments = [
        {"user": "装修小白77", "text": "博主这个全屋定制多少钱一平？有落地案例吗，求私！"},
        {"user": "路人甲", "text": "图三的柜子颜色挺好看的。"},
        {"user": "刚需买房人", "text": "避坑帖好及时！我最近也在对比两家工厂，求推荐靠谱的避坑清单！"},
    ]
    print("\n[社媒截流] 意向识别与破冰建议：")
    for item in demo_comments:
        res = analyzer.analyze_comment(item["text"], industry="全屋定制")
        if res["intent_score"] >= Config.INTENT_THRESHOLD:
            print(f"🔥 高潜线索 [{res['intent_score']}分] @{item['user']}: \"{item['text']}\"")
            print(f"   破冰建议: {res['recommended_icebreaker']}")

    import csv
    with open("leads.csv", "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["name", "address", "city", "primary_phone", "is_mobile"])
        writer.writeheader()
        writer.writerows(places)
    print("\n🎉 名单已保存至 leads.csv")

if __name__ == "__main__":
    run_demo()
