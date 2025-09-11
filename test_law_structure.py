#!/usr/bin/env python3
"""
법령 구조 라벨링 규칙 테스트
"""

import json
from pathlib import Path
from src.core.rule_validator import RuleValidator

def test_law_structure():
    """법령 구조 라벨링 테스트"""
    
    # 테스트 데이터 생성
    test_data = {
        "elements": [
            {
                "id": "law1",
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "헌법신체운동법"},
                "pageIndex": 0
            },
            {
                "id": "part1", 
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "제52편 총칙과 선거"},
                "pageIndex": 0
            },
            {
                "id": "chapter1",
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "제301장 헌법선거운동"},
                "pageIndex": 0
            },
            {
                "id": "section1",
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "제1절 선발선수운동과의 공지"},
                "pageIndex": 0
            },
            {
                "id": "article1",
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "제3010조 선발의 기준과 사용되는 절차"},
                "pageIndex": 0
            },
            {
                "id": "item1",
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "(1) 선거(election)를 통한 다음을 말한다"},
                "pageIndex": 0
            },
            {
                "id": "item2",
                "category": {"label": "ParaText", "type": "PARAGRAPH"},
                "content": {"text": "(2) 후보자(candidate)라 함은 연방공정심지역 정한 또는 후보자 지명을 구하는 자를 말하며"},
                "pageIndex": 0
            }
        ]
    }
    
    # 검증 실행
    validator = RuleValidator()
    issues = validator.validate_all_rules(test_data, "test_law.json")
    
    print("\n=== 법령 구조 라벨링 규칙 테스트 결과 ===")
    print(f"발견된 이슈: {len(issues)}개\n")
    
    for issue in issues:
        print(f"{issue}")
        if issue.suggested_fix:
            print(f"  제안된 수정: {issue.suggested_fix}")
        if 'target_type' in issue.metadata:
            print(f"  타입 변경: → {issue.metadata['target_type']}")
        print()

if __name__ == "__main__":
    test_law_structure()
