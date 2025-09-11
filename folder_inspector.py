#!/usr/bin/env python3
"""
폴더 구조 복사 및 문제 패턴 검수 도구
"""

import os
import shutil
import zipfile
import json
import argparse
from pathlib import Path
from typing import List, Dict, Any, Tuple
from datetime import datetime

class FolderInspector:
    """폴더 검수 및 복사 도구"""
    
    def __init__(self, source_dir: Path, target_base_dir: Path):
        self.source_dir = Path(source_dir)
        self.target_base_dir = Path(target_base_dir)
        self.issues = []
        
    def create_target_structure(self) -> Path:
        """대상 폴더 구조 생성"""
        # 검수 폴더명 생성 (소스 폴더명_검수)
        source_name = self.source_dir.name
        target_name = f"{source_name}_검수"
        target_dir = self.target_base_dir / target_name
        
        # 대상 디렉토리가 이미 있으면 삭제 후 재생성
        if target_dir.exists():
            shutil.rmtree(target_dir)
        
        # 폴더 구조 복사
        shutil.copytree(self.source_dir, target_dir)
        print(f"📁 폴더 구조 복사 완료: {self.source_dir} → {target_dir}")
        
        return target_dir
    
    def find_zip_files(self, directory: Path) -> List[Path]:
        """ZIP 파일 찾기"""
        zip_files = []
        for file_path in directory.rglob("*.zip"):
            zip_files.append(file_path)
        return zip_files
    
    def extract_and_check_zip(self, zip_path: Path) -> List[Dict[str, Any]]:
        """ZIP 파일 추출 및 검사"""
        issues = []
        temp_extract_dir = zip_path.parent / f"temp_{zip_path.stem}"
        
        try:
            # ZIP 파일 추출
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(temp_extract_dir)
            
            # visualinfo 폴더에서 JSON 파일 찾기
            visualinfo_dir = temp_extract_dir / "visualinfo"
            if visualinfo_dir.exists():
                for json_file in visualinfo_dir.glob("*.json"):
                    file_issues = self.check_json_file(json_file, zip_path.name)
                    issues.extend(file_issues)
            
        except Exception as e:
            issues.append({
                'zip_file': zip_path.name,
                'error': f"ZIP 파일 처리 오류: {e}",
                'type': 'zip_error'
            })
        
        finally:
            # 임시 폴더 정리
            if temp_extract_dir.exists():
                shutil.rmtree(temp_extract_dir)
        
        return issues
    
    def check_json_file(self, json_file: Path, zip_name: str) -> List[Dict[str, Any]]:
        """JSON 파일 내용 검사"""
        issues = []
        
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            elements = data.get('elements', [])
            
            for i, element in enumerate(elements):
                text = element.get('content', {}).get('text', '').strip()
                label = element.get('category', {}).get('label', '')
                element_id = element.get('id', f'element_{i}')
                
                if not text:
                    continue
                
                # 문제 패턴 검사
                found_issues = self.check_text_patterns(text, label, element_id, zip_name, json_file.name)
                issues.extend(found_issues)
                
        except Exception as e:
            issues.append({
                'zip_file': zip_name,
                'json_file': json_file.name,
                'error': f"JSON 파일 읽기 오류: {e}",
                'type': 'json_error'
            })
        
        return issues
    
    def check_text_patterns(self, text: str, label: str, element_id: str, zip_name: str, json_name: str) -> List[Dict[str, Any]]:
        """텍스트 패턴 문제 검사"""
        issues = []
        
        # 1. 이상한 문자나 기호 패턴
        suspicious_patterns = [
            ('□□□', '연속된 □ 기호'),
            ('???', '연속된 물음표'),
            ('###', '연속된 # 기호'),
            ('...', '연속된 점'),
            ('   ', '과도한 공백'),
            ('\n\n\n', '과도한 줄바꿈'),
            ('ㅁㅁㅁ', '의미없는 한글 반복'),
        ]
        
        for pattern, description in suspicious_patterns:
            if pattern in text:
                issues.append({
                    'zip_file': zip_name,
                    'json_file': json_name,
                    'element_id': element_id,
                    'issue_type': 'suspicious_pattern',
                    'pattern': pattern,
                    'description': description,
                    'text_preview': text[:100] + '...' if len(text) > 100 else text,
                    'current_label': label
                })
        
        # 2. 잘못된 라벨링 패턴 (우리가 만든 규칙 기반)
        labeling_issues = self.check_labeling_patterns(text, label)
        for issue in labeling_issues:
            issue.update({
                'zip_file': zip_name,
                'json_file': json_name,
                'element_id': element_id,
                'text_preview': text[:50] + '...' if len(text) > 50 else text
            })
            issues.append(issue)
        
        return issues
    
    def check_labeling_patterns(self, text: str, label: str) -> List[Dict[str, Any]]:
        """라벨링 패턴 문제 검사"""
        issues = []
        
        # R001: 원문/번역문이 ListText인 경우
        if "원문" in text or "번역문" in text:
            if label == "ListText":
                issues.append({
                    'issue_type': 'wrong_label',
                    'rule': 'R001',
                    'description': '원문/번역문이 ListText로 라벨링됨',
                    'suggested_label': 'ParaText',
                    'current_label': label
                })
        
        # R003: 법령 구조 라벨링
        import re
        
        # ~법 패턴
        if re.search(r'[가-힣]+법$', text) and label != 'ParaTitle':
            issues.append({
                'issue_type': 'wrong_label',
                'rule': 'R003',
                'description': '법률명이 ParaTitle이 아님',
                'suggested_label': 'ParaTitle',
                'current_label': label
            })
        
        # 제~편, 제~장, 제~절, 제~조 패턴
        law_patterns = [
            (r'^제\s*\d+\s*편', '편'),
            (r'^제\s*\d+\s*장', '장'),
            (r'^제\s*\d+\s*절', '절'),
            (r'^제\s*\d+\s*조', '조')
        ]
        
        for pattern, unit in law_patterns:
            if re.search(pattern, text) and label != 'ParaTitle':
                issues.append({
                    'issue_type': 'wrong_label',
                    'rule': 'R003',
                    'description': f'제{unit} 구조가 ParaTitle이 아님',
                    'suggested_label': 'ParaTitle',
                    'current_label': label
                })
        
        # R004: 한글 인코딩 오류 검출
        # 한글 깨짐 패턴들
        corrupted_patterns = [
            (r'[A-Z]{4,}[0-9]*', '한글 깨짐 (대문자+숫자)'),
            (r'[A-Z]+CD[0-9]*', '한글 깨짐 (CD 패턴)'),
            (r'[A-Z]+EE[A-Z]*', '한글 깨짐 (EE 패턴)'),
            (r'\b[A-Z]{6,}\b', '한글 깨짐 (연속 대문자)'),
        ]
        
        for pattern, desc in corrupted_patterns:
            if re.search(pattern, text):
                issues.append({
                    'issue_type': 'encoding_error',
                    'rule': 'R004',
                    'description': f'{desc}: 인코딩 오류 의심',
                    'suggested_action': '텍스트 인코딩 확인 필요',
                    'problematic_text': text[:50]
                })
        
        # 잘못된 특수문자 검사
        if re.search(r'[^\w\s가-힣\[\]().,!?;:\'"<>{}|\\/@#$%^&*+=~`-]', text):
            issues.append({
                'issue_type': 'encoding_error',
                'rule': 'R004',
                'description': '잘못된 문자 포함',
                'suggested_action': '문자 인코딩 수정 필요',
                'problematic_text': text[:50]
            })
        
        # (1), (2) 등의 번호 패턴
        if (re.search(r'^\s*\(\d+\)', text) or 
            re.search(r'^\s*\d+\.', text) or 
            re.search(r'^\s*[가-힣]\.', text)) and label != 'ListText':
            issues.append({
                'issue_type': 'wrong_label',
                'rule': 'R003',
                'description': '번호 항목이 ListText가 아님',
                'suggested_label': 'ListText',
                'current_label': label
            })
        
        return issues
    
    def process_folder(self) -> Tuple[Path, List[Dict[str, Any]]]:
        """전체 폴더 처리"""
        print(f"🔍 검수 시작: {self.source_dir}")
        
        # 1. 폴더 구조 복사
        target_dir = self.create_target_structure()
        
        # 2. ZIP 파일들 찾기
        zip_files = self.find_zip_files(target_dir)
        print(f"📦 발견된 ZIP 파일: {len(zip_files)}개")
        
        # 3. 각 ZIP 파일 검사
        all_issues = []
        for i, zip_file in enumerate(zip_files, 1):
            print(f"[{i}/{len(zip_files)}] 검사 중: {zip_file.name}")
            issues = self.extract_and_check_zip(zip_file)
            all_issues.extend(issues)
        
        return target_dir, all_issues
    
    def generate_report(self, target_dir: Path, issues: List[Dict[str, Any]]) -> None:
        """검수 보고서 생성"""
        report_file = target_dir / "검수_보고서.txt"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("=" * 60 + "\n")
            f.write(f"검수 보고서 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 60 + "\n\n")
            
            f.write(f"검수 대상: {self.source_dir}\n")
            f.write(f"검수 결과: {target_dir}\n")
            f.write(f"총 발견된 이슈: {len(issues)}개\n\n")
            
            if not issues:
                f.write("✅ 문제가 발견되지 않았습니다.\n")
                return
            
            # 이슈 유형별 분류
            issue_types = {}
            for issue in issues:
                issue_type = issue.get('issue_type', 'unknown')
                if issue_type not in issue_types:
                    issue_types[issue_type] = []
                issue_types[issue_type].append(issue)
            
            # 유형별 리포트
            for issue_type, type_issues in issue_types.items():
                f.write(f"\n📋 {issue_type.upper()} ({len(type_issues)}개)\n")
                f.write("-" * 50 + "\n")
                
                for issue in type_issues:
                    f.write(f"파일: {issue['zip_file']}\n")
                    if 'json_file' in issue:
                        f.write(f"JSON: {issue['json_file']}\n")
                    if 'element_id' in issue:
                        f.write(f"요소: {issue['element_id']}\n")
                    if 'description' in issue:
                        f.write(f"문제: {issue['description']}\n")
                    if 'suggested_label' in issue:
                        f.write(f"제안: {issue['current_label']} → {issue['suggested_label']}\n")
                    if 'text_preview' in issue:
                        f.write(f"내용: {issue['text_preview']}\n")
                    f.write("\n")
        
        print(f"📄 검수 보고서 생성: {report_file}")


def main():
    parser = argparse.ArgumentParser(description="폴더 구조 복사 및 문제 패턴 검수")
    parser.add_argument("source", help="검수할 소스 폴더 경로")
    parser.add_argument("--target", default=r"C:\Users\User\Documents\검수", 
                       help="대상 기본 폴더 (기본값: C:\\Users\\User\\Documents\\검수)")
    
    args = parser.parse_args()
    
    source_dir = Path(args.source)
    target_base_dir = Path(args.target)
    
    if not source_dir.exists():
        print(f"❌ 소스 폴더를 찾을 수 없습니다: {source_dir}")
        return
    
    # 대상 기본 폴더 생성
    target_base_dir.mkdir(parents=True, exist_ok=True)
    
    # 검수 실행
    inspector = FolderInspector(source_dir, target_base_dir)
    target_dir, issues = inspector.process_folder()
    
    # 보고서 생성
    inspector.generate_report(target_dir, issues)
    
    # 결과 출력
    print(f"\n🎉 검수 완료!")
    print(f"📁 결과 폴더: {target_dir}")
    print(f"🔍 발견된 이슈: {len(issues)}개")
    
    if issues:
        print("\n주요 이슈:")
        issue_summary = {}
        for issue in issues:
            key = issue.get('description', issue.get('issue_type', 'unknown'))
            issue_summary[key] = issue_summary.get(key, 0) + 1
        
        for desc, count in list(issue_summary.items())[:10]:
            print(f"  - {desc}: {count}개")


if __name__ == "__main__":
    main()
