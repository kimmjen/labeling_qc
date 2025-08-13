#!/usr/bin/env python3
"""
검수 비교 도구 - 자동 검수 결과와 수동 검수 결과를 비교
"""

import json
import sys
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.quality_controller import QualityController
from src.models.quality_issue import QualityIssue
from src.utils.zip_processor import ZipProcessor


@dataclass
class ComparisonResult:
    """비교 결과 데이터 클래스"""
    file_path: str
    auto_issues: List[QualityIssue]
    manual_fixed: bool
    differences: List[str]
    accuracy_score: float


class QualityComparator:
    """품질 검수 비교기"""
    
    def __init__(self):
        self.controller = QualityController()
        self.zip_processor = ZipProcessor()
    
    def compare_directories(self, target_dir: Path, completed_dir: Path) -> List[ComparisonResult]:
        """디렉토리 비교"""
        results = []
        
        # ZIP 파일이 있는 경우 자동 추출
        target_json_files = self._get_json_files(target_dir, "target")
        completed_json_files = self._get_json_files(completed_dir, "completed")
        
        print(f"🔍 검수 대상 파일 {len(target_json_files)}개 발견")
        print(f"🔍 검수 완료 파일 {len(completed_json_files)}개 발견")
        
        # 파일명으로 매칭
        target_file_dict = {self._get_file_key(f): f for f in target_json_files}
        completed_file_dict = {self._get_file_key(f): f for f in completed_json_files}
        
        for file_key, target_file in target_file_dict.items():
            if file_key in completed_file_dict:
                completed_file = completed_file_dict[file_key]
                result = self._compare_single_file(target_file, completed_file)
                results.append(result)
                print(f"✅ 비교 완료: {file_key}")
            else:
                print(f"⚠️ 검수완료 파일 없음: {file_key}")
        
        return results
    
    def _get_json_files(self, directory: Path, label: str) -> List[Path]:
        """디렉토리에서 JSON 파일 추출"""
        json_files = []
        
        # 직접 JSON 파일 찾기
        direct_json = list(directory.rglob("*.json"))
        if direct_json:
            json_files.extend(direct_json)
            print(f"📄 {label} 디렉토리에서 직접 JSON 파일 {len(direct_json)}개 발견")
        
        # ZIP 파일이 있으면 추출
        zip_files = list(directory.rglob("*.zip"))
        if zip_files:
            print(f"📦 {label} 디렉토리에서 ZIP 파일 {len(zip_files)}개 발견, 추출 중...")
            extracted_json = self.zip_processor.process_directory(directory)
            json_files.extend(extracted_json)
        
        return json_files
    
    def _get_file_key(self, file_path: Path) -> str:
        """파일 매칭용 키 생성"""
        # visualinfo 파일명에서 고유 식별자 추출
        name = file_path.name
        if "_visualinfo" in name:
            # "FLAW2023000592_visualinfo.json" → "FLAW2023000592"
            return name.split("_visualinfo")[0]
        else:
            return file_path.stem
    
    def _compare_single_file(self, target_file: Path, completed_file: Path) -> ComparisonResult:
        """단일 파일 비교"""
        # 자동 검수 실행
        auto_issues = self.controller.validate_file(target_file)
        
        # 원본과 검수완료 파일 비교
        differences = self._find_differences(target_file, completed_file)
        
        # 정확도 계산
        accuracy = self._calculate_accuracy(auto_issues, differences)
        
        return ComparisonResult(
            file_path=str(target_file.name),
            auto_issues=auto_issues,
            manual_fixed=len(differences) > 0,
            differences=differences,
            accuracy_score=accuracy
        )
    
    def _find_differences(self, target_file: Path, completed_file: Path) -> List[str]:
        """파일 간 차이점 찾기"""
        differences = []
        
        try:
            with open(target_file, 'r', encoding='utf-8') as f:
                target_data = json.load(f)
            
            with open(completed_file, 'r', encoding='utf-8') as f:
                completed_data = json.load(f)
            
            # 요소별 비교
            target_elements = {e.get('id'): e for e in target_data.get('elements', [])}
            completed_elements = {e.get('id'): e for e in completed_data.get('elements', [])}
            
            # 라벨 변경 확인
            for element_id, target_element in target_elements.items():
                if element_id in completed_elements:
                    completed_element = completed_elements[element_id]
                    
                    target_label = target_element.get('category', {}).get('label', '')
                    completed_label = completed_element.get('category', {}).get('label', '')
                    
                    if target_label != completed_label:
                        text = target_element.get('content', {}).get('text', '')[:30]
                        differences.append(f"라벨 변경: {element_id} '{text}...' {target_label} → {completed_label}")
            
            # 요소 추가/제거 확인
            added_elements = set(completed_elements.keys()) - set(target_elements.keys())
            removed_elements = set(target_elements.keys()) - set(completed_elements.keys())
            
            for element_id in added_elements:
                differences.append(f"요소 추가: {element_id}")
            
            for element_id in removed_elements:
                differences.append(f"요소 제거: {element_id}")
        
        except Exception as e:
            differences.append(f"파일 비교 오류: {str(e)}")
        
        return differences
    
    def _calculate_accuracy(self, auto_issues: List[QualityIssue], manual_differences: List[str]) -> float:
        """정확도 계산"""
        if not manual_differences:
            # 수동 수정이 없고 자동 검수에서도 이슈가 없으면 100%
            return 100.0 if not auto_issues else 90.0
        
        # 자동 검수가 발견한 이슈와 수동 수정이 얼마나 일치하는지 계산
        auto_label_issues = [issue for issue in auto_issues if 'label' in issue.message.lower()]
        manual_label_changes = [diff for diff in manual_differences if '라벨 변경' in diff]
        
        if not auto_label_issues and not manual_label_changes:
            return 100.0
        
        if not auto_label_issues:
            return 50.0  # 자동 검수가 놓친 경우
        
        if not manual_label_changes:
            return 70.0  # 자동 검수가 과검출한 경우
        
        # 간단한 일치도 계산
        match_ratio = min(len(auto_label_issues), len(manual_label_changes)) / max(len(auto_label_issues), len(manual_label_changes))
        return match_ratio * 100
    
    def generate_comparison_report(self, results: List[ComparisonResult]) -> Dict[str, Any]:
        """비교 보고서 생성"""
        total_files = len(results)
        files_with_manual_fixes = sum(1 for r in results if r.manual_fixed)
        
        # 정확도 통계
        accuracies = [r.accuracy_score for r in results]
        avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0
        
        # 이슈 통계
        total_auto_issues = sum(len(r.auto_issues) for r in results)
        total_manual_changes = sum(len(r.differences) for r in results)
        
        # 가장 많은 이슈가 있는 파일들
        top_issue_files = sorted(results, key=lambda r: len(r.auto_issues), reverse=True)[:5]
        
        return {
            "summary": {
                "total_files": total_files,
                "files_with_manual_fixes": files_with_manual_fixes,
                "manual_fix_rate": (files_with_manual_fixes / total_files * 100) if total_files > 0 else 0,
                "average_accuracy": avg_accuracy,
                "total_auto_issues": total_auto_issues,
                "total_manual_changes": total_manual_changes
            },
            "accuracy_distribution": {
                "high_accuracy": sum(1 for a in accuracies if a >= 80),
                "medium_accuracy": sum(1 for a in accuracies if 60 <= a < 80),
                "low_accuracy": sum(1 for a in accuracies if a < 60)
            },
            "top_issue_files": [
                {
                    "file": r.file_path,
                    "auto_issues_count": len(r.auto_issues),
                    "manual_changes_count": len(r.differences),
                    "accuracy": r.accuracy_score
                }
                for r in top_issue_files
            ],
            "detailed_results": [
                {
                    "file": r.file_path,
                    "auto_issues": [issue.to_dict() for issue in r.auto_issues],
                    "manual_differences": r.differences,
                    "accuracy_score": r.accuracy_score
                }
                for r in results
            ]
        }
    
    def print_summary(self, report: Dict[str, Any]):
        """요약 출력"""
        summary = report["summary"]
        
        print("\n" + "="*60)
        print("📊 검수 비교 결과 요약")
        print("="*60)
        
        print(f"📁 총 비교 파일 수: {summary['total_files']}개")
        print(f"🔧 수동 수정 파일 수: {summary['files_with_manual_fixes']}개 ({summary['manual_fix_rate']:.1f}%)")
        print(f"🎯 평균 정확도: {summary['average_accuracy']:.1f}%")
        print(f"🔍 자동 검출 이슈: {summary['total_auto_issues']}개")
        print(f"✏️ 수동 수정 사항: {summary['total_manual_changes']}개")
        
        print(f"\n📈 정확도 분포:")
        acc_dist = report["accuracy_distribution"]
        print(f"  높음 (80% 이상): {acc_dist['high_accuracy']}개")
        print(f"  보통 (60-79%): {acc_dist['medium_accuracy']}개")
        print(f"  낮음 (60% 미만): {acc_dist['low_accuracy']}개")
        
        print(f"\n🔥 이슈가 많은 상위 파일:")
        for i, file_info in enumerate(report["top_issue_files"][:3], 1):
            print(f"  {i}. {Path(file_info['file']).name}")
            print(f"     자동검출: {file_info['auto_issues_count']}개, 수동수정: {file_info['manual_changes_count']}개")
            print(f"     정확도: {file_info['accuracy']:.1f}%")


def main():
    """메인 함수"""
    # 검수 대상 폴더
    target_dir = Path(r"C:\Users\User\Downloads\250812_전체_박선화\1페이지-그림+비교표+테이블 삽입")
    
    # 검수 완료 폴더  
    completed_dir = Path(r"C:\Users\User\Documents\검수\20250813-박선화\1페이지-그림+비교표+테이블 삽입")
    
    if not target_dir.exists():
        print(f"❌ 검수 대상 폴더를 찾을 수 없습니다: {target_dir}")
        return
    
    if not completed_dir.exists():
        print(f"❌ 검수 완료 폴더를 찾을 수 없습니다: {completed_dir}")
        return
    
    print("🚀 검수 비교 시작")
    print(f"📂 검수 대상: {target_dir}")
    print(f"📂 검수 완료: {completed_dir}")
    
    # 비교 실행
    comparator = QualityComparator()
    results = comparator.compare_directories(target_dir, completed_dir)
    
    # 보고서 생성
    report = comparator.generate_comparison_report(results)
    
    # 결과 출력
    comparator.print_summary(report)
    
    # 상세 보고서 저장
    report_file = Path("quality_comparison_report.json")
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n💾 상세 보고서 저장: {report_file}")


if __name__ == "__main__":
    main()
