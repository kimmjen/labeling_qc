#!/usr/bin/env python3
"""
품질 검증 실행 스크립트
"""

import json
from pathlib import Path
from src.core.rule_validator import RuleValidator

def main():
    # 검증기 초기화
    validator = RuleValidator()
    
    # raw 데이터 파일 로드
    raw_file = Path("data/raw/sample.json")
    with open(raw_file, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # 규칙 검증 실행
    print("\n=== Raw 데이터 검증 결과 ===")
    issues = validator.validate_all_rules(raw_data, str(raw_file))
    
    # 결과 출력
    if issues:
        print(f"\n발견된 이슈: {len(issues)}개")
        for issue in issues:
            print(f"\n{issue}")
            if issue.suggested_fix:
                print(f"제안된 수정: {issue.suggested_fix}")
    else:
        print("이슈가 발견되지 않았습니다.")

if __name__ == "__main__":
    main()
