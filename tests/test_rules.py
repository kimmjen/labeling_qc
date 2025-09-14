#!/usr/bin/env python3
"""
라벨링 규칙 테스트
"""

import unittest
from backend.src.core.rule_validator import RuleValidator

class TestRuleValidator(unittest.TestCase):
    def setUp(self):
        self.validator = RuleValidator()
        
    def test_rule_validation(self):
        # 테스트 데이터 생성
        test_data = {
            "elements": [
                {
                    "id": "title1",
                    "category": {"label": "RegionTitle"},
                    "content": {"text": "회장응수집 원본원칙"},
                    "pageIndex": 0
                },
                {
                    "id": "text1",
                    "category": {"label": "ListText"},
                    "content": {"text": "원문"},
                    "pageIndex": 0
                },
                {
                    "id": "title2",
                    "category": {"label": "RegionTitle"},
                    "content": {"text": "□ 제1장"},
                    "pageIndex": 0
                },
                {
                    "id": "text2",
                    "category": {"label": "ListText"},
                    "content": {"text": "번역문"},
                    "pageIndex": 0
                }
            ]
        }
        
        # 규칙 검증 실행
        issues = self.validator.validate_all_rules(test_data, "test.json")
        
        # 결과 출력
        print("\n=== 검증 결과 ===")
        for issue in issues:
            print(f"{issue}\n")
            
        # 검증
        # 1. ListText → ParaText 변경 이슈 (원문, 번역문)
        list_to_para = [i for i in issues if i.rule_id == "R001"]
        self.assertEqual(len(list_to_para), 2, "원문과 번역문 모두 ParaText로 변경되어야 함")
        
        # 2. RegionTitle → ParaTitle 변경 이슈
        region_to_para = [i for i in issues if i.rule_id == "R002"]
        self.assertEqual(len(region_to_para), 1, "숫자나 □가 없는 RegionTitle만 ParaTitle로 변경되어야 함")

if __name__ == '__main__':
    unittest.main()
