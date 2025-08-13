#!/usr/bin/env python3
"""
라벨링 룰 기반 자동 수정 도구
- 정의된 룰에 따른 자동 수정
- 라벨 타입 변경
- 불필요한 요소 제거
- 순서 재정렬
"""

import re
import json
import copy
from pathlib import Path
from typing import List, Dict, Any, Tuple

from ..models.quality_issue import FixResult


class RuleBasedFixer:
    """룰 기반 자동 수정기"""
    
    def __init__(self, extract_dir: Path):
        self.extract_dir = extract_dir
        self.visualinfo_file = None
        self.visualinfo_data = {}
        
        # visualinfo 파일 찾기
        visualinfo_files = list((extract_dir / "visualinfo").glob("*_visualinfo.json"))
        if visualinfo_files:
            self.visualinfo_file = visualinfo_files[0]
            with open(self.visualinfo_file, 'r', encoding='utf-8') as f:
                self.visualinfo_data = json.load(f)
    
    def fix_unnecessary_elements(self) -> List[FixResult]:
        """불필요한 요소 제거"""
        fixes = []
        
        if not self.visualinfo_data:
            return fixes
        
        elements = self.visualinfo_data.get('elements', [])
        original_count = len(elements)
        
        # 불필요한 텍스트 패턴
        unnecessary_patterns = [
            r"The\s*현안",
            r"첨부자료", 
            r"참고자료",
            r"별첨",
            r"^로그",
            r"헤더.*정보"
        ]
        
        # 제거할 요소들 찾기
        elements_to_remove = []
        for i, element in enumerate(elements):
            text = element.get('content', {}).get('text', '')
            if not text:
                continue
                
            for pattern in unnecessary_patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    elements_to_remove.append(i)
                    break
        
        # 뒤에서부터 제거 (인덱스 변경 방지)
        for i in reversed(elements_to_remove):
            removed_element = elements.pop(i)
            fixes.append(FixResult(
                success=True,
                description=f"불필요한 요소 제거: {removed_element.get('content', {}).get('text', '')[:30]}...",
                before_value="present",
                after_value="removed"
            ))
        
        if fixes:
            self.visualinfo_data['elements'] = elements
        
        return fixes
    
    def fix_label_types(self) -> List[FixResult]:
        """라벨 타입 자동 수정"""
        fixes = []
        
        if not self.visualinfo_data:
            return fixes
        
        elements = self.visualinfo_data.get('elements', [])
        
        for element in elements:
            text = element.get('content', {}).get('text', '').strip()
            current_label = element.get('category', {}).get('label', '')
            
            # 제목 패턴 감지 및 수정
            new_label = self._determine_correct_label(text, current_label, element)
            
            if new_label and new_label != current_label:
                old_label = current_label
                element['category']['label'] = new_label
                
                fixes.append(FixResult(
                    success=True,
                    description=f"라벨 타입 수정: {text[:30]}...",
                    before_value=old_label,
                    after_value=new_label
                ))
        
        return fixes
    
    def _determine_correct_label(self, text: str, current_label: str, element: Dict) -> str:
        """올바른 라벨 타입 결정"""
        if not text:
            return current_label
        
        text = text.strip()
        
        # R009: '원문' / '번역문'이면서 ListText인 경우 ParaText로 변경
        if text in {"원문", "번역문"} and current_label == "ListText":
            # 타입도 함께 변경
            if 'category' in element and 'type' in element['category']:
                element['category']['type'] = 'PARAGRAPH'
            return 'ParaText'
        
        return current_label
    
    def _is_legal_content(self, text: str) -> bool:
        """법령 관련 내용인지 판단"""
        legal_keywords = [
            '법', '령', '조', '항', '호', '규정', '조례',
            '시행령', '시행규칙', '법률', '정령', '고시'
        ]
        
        return any(keyword in text for keyword in legal_keywords)
    
    def fix_element_order(self) -> List[FixResult]:
        """요소 순서 정렬"""
        fixes = []
        
        if not self.visualinfo_data:
            return fixes
        
        elements = self.visualinfo_data.get('elements', [])
        original_order = [e.get('id') for e in elements]
        
        # 페이지별로 그룹화 후 Y좌표 기준 정렬
        page_groups = {}
        for element in elements:
            page_idx = element.get('pageIndex', 0)
            if page_idx not in page_groups:
                page_groups[page_idx] = []
            page_groups[page_idx].append(element)
        
        sorted_elements = []
        for page_idx in sorted(page_groups.keys()):
            page_elements = page_groups[page_idx]
            
            # Y좌표 기준 정렬 (위에서 아래로)
            page_elements.sort(key=lambda e: e.get('bbox', {}).get('top', 0))
            sorted_elements.extend(page_elements)
        
        new_order = [e.get('id') for e in sorted_elements]
        
        if original_order != new_order:
            self.visualinfo_data['elements'] = sorted_elements
            fixes.append(FixResult(
                success=True,
                description="요소 순서 정렬 완료",
                before_value=f"원본 순서: {len(original_order)}개 요소",
                after_value=f"정렬된 순서: {len(new_order)}개 요소"
            ))
        
        return fixes
    
    def fix_table_structure(self) -> List[FixResult]:
        """테이블 구조 수정"""
        fixes = []
        
        if not self.visualinfo_data:
            return fixes
        
        elements = self.visualinfo_data.get('elements', [])
        table_elements = [e for e in elements if e.get('category', {}).get('type') == 'TABLE']
        
        for table in table_elements:
            table_data = table.get('table', {})
            cells = table_data.get('cells', [])
            
            if not cells:
                continue
            
            # 원문/번역문 테이블 처리
            if self._is_translation_table(table):
                fixed_table = self._fix_translation_table_order(table)
                if fixed_table != table:
                    # 테이블 업데이트
                    table.update(fixed_table)
                    fixes.append(FixResult(
                        success=True,
                        description="원문/번역문 테이블 순서 수정",
                        before_value="원본 순서",
                        after_value="원문→번역문→원문내용→번역문내용 순서"
                    ))
        
        return fixes
    
    def _is_translation_table(self, table: Dict) -> bool:
        """원문/번역문 테이블인지 판단"""
        text = table.get('content', {}).get('text', '')
        return '원문' in text and '번역' in text
    
    def _fix_translation_table_order(self, table: Dict) -> Dict:
        """원문/번역문 테이블 순서 수정"""
        # 복잡한 테이블 구조 수정은 여기서 구현
        # 현재는 간단한 예시만 제공
        fixed_table = copy.deepcopy(table)
        
        # TODO: 실제 테이블 셀 순서 재정렬 로직 구현
        # 원문 → 번역문 → 원문내용 → 번역문내용 순서로 정렬
        
        return fixed_table
    
    def remove_forbidden_tags(self) -> List[FixResult]:
        """금지된 태그 제거"""
        fixes = []
        
        if not self.visualinfo_data:
            return fixes
        
        elements = self.visualinfo_data.get('elements', [])
        forbidden_tags = ['연결', '국가명', '정책명', '법률명', '요약']
        
        for element in elements:
            # 태그 정보가 있다면 제거
            tags = element.get('tags', [])
            if isinstance(tags, list):
                original_tags = tags.copy()
                cleaned_tags = [tag for tag in tags if tag not in forbidden_tags]
                
                if len(cleaned_tags) != len(original_tags):
                    element['tags'] = cleaned_tags
                    removed_tags = [tag for tag in original_tags if tag not in cleaned_tags]
                    
                    fixes.append(FixResult(
                        success=True,
                        description=f"금지된 태그 제거: {', '.join(removed_tags)}",
                        before_value=original_tags,
                        after_value=cleaned_tags
                    ))
        
        return fixes
    
    def run_all_rule_fixes(self) -> Dict[str, List[FixResult]]:
        """모든 룰 기반 수정 실행"""
        all_fixes = {}
        
        print("  불필요한 요소 제거 중...")
        all_fixes['unnecessary'] = self.fix_unnecessary_elements()
        
        print("  라벨 타입 수정 중...")
        all_fixes['labels'] = self.fix_label_types()
        
        # 순서 정렬 비활성화 (기존 순서 유지)
        # print("  요소 순서 정렬 중...")
        # all_fixes['order'] = self.fix_element_order()
        all_fixes['order'] = []
        
        print("  테이블 구조 수정 중...")
        all_fixes['tables'] = self.fix_table_structure()
        
        print("  금지된 태그 제거 중...")
        all_fixes['tags'] = self.remove_forbidden_tags()
        
        return all_fixes
    
    def save_fixes(self) -> bool:
        """수정된 결과 저장 (백업 없이)"""
        if not self.visualinfo_file or not self.visualinfo_data:
            return False
        
        try:
            # 수정된 데이터 저장
            with open(self.visualinfo_file, 'w', encoding='utf-8') as f:
                json.dump(self.visualinfo_data, f, ensure_ascii=False, indent=2)
            
            return True
            
        except Exception as e:
            print(f"룰 기반 수정 결과 저장 실패: {e}")
            return False


def main():
    """테스트용 메인 함수"""
    extract_dir = Path("test_data")
    
    if not extract_dir.exists():
        print("테스트 데이터 디렉토리를 찾을 수 없습니다.")
        return
    
    fixer = RuleBasedFixer(extract_dir)
    fixes = fixer.run_all_rule_fixes()
    
    # 수정 결과 저장
    if any(fixes.values()):
        if fixer.save_fixes():
            print("✅ 룰 기반 수정 결과가 저장되었습니다.")
        else:
            print("❌ 룰 기반 수정 결과 저장에 실패했습니다.")
    
    # 결과 출력
    total_fixes = sum(len(fix_list) for fix_list in fixes.values())
    print(f"\n🔧 총 {total_fixes}개 항목이 룰 기반으로 수정되었습니다.")
    
    for category, fix_list in fixes.items():
        if fix_list:
            print(f"\n📋 {category.upper()} 수정 결과:")
            for fix in fix_list:
                status = "✅" if fix.success else "❌"
                print(f"  {status} {fix.description}")


if __name__ == "__main__":
    main()
