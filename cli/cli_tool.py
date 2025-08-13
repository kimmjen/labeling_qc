#!/usr/bin/env python3
"""
CLI 도구 - 품질 검수 명령행 인터페이스
"""

import argparse
import sys
import time
import json
from pathlib import Path

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.quality_controller import QualityController
from src.utils.quality_comparator import QualityComparator
from src.utils.zip_processor import ZipProcessor
from src.utils.zip_recompressor import ZipRecompressor
from src.core.rule_fixer import RuleBasedFixer


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(description="라벨링 품질 검수 도구")
    parser.add_argument("path", help="검수할 파일 또는 디렉토리 경로")
    parser.add_argument("--validate", "-v", action="store_true", help="품질 검증만 실행")
    parser.add_argument("--fix", "-f", action="store_true", help="자동 수정 실행")
    parser.add_argument("--report", "-r", help="보고서 저장 경로")
    parser.add_argument("--compare", "-c", help="검수 완료 폴더와 비교")
    parser.add_argument("--auto-fix", action="store_true", help="자동 수정 실행")
    parser.add_argument("--recompress", action="store_true", help="수정 후 ZIP 재압축")
    parser.add_argument("--full-workflow", action="store_true", help="전체 워크플로우 (추출→수정→재압축)")
    parser.add_argument("--process-to-review", action="store_true", help="지정 폴더에 '검수' 폴더 생성하여 수정된 파일 저장")
    parser.add_argument("--verbose", action="store_true", help="상세 출력")
    
    args = parser.parse_args()
    
    # 경로 검증
    target_path = Path(args.path)
    if not target_path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {target_path}")
        sys.exit(1)
    
    # 컨트롤러 초기화
    controller = QualityController()
    
    # 비교 모드
    if args.compare:
        comparator = QualityComparator()
        completed_dir = Path(args.compare)
        
        if not completed_dir.exists():
            print(f"❌ 검수완료 폴더를 찾을 수 없습니다: {completed_dir}")
            sys.exit(1)
        
        print(f"🔍 검수 비교 시작")
        print(f"📂 검수 대상: {target_path}")
        print(f"📂 검수 완료: {completed_dir}")
        
        results = comparator.compare_directories(target_path, completed_dir)
        report = comparator.generate_comparison_report(results)
        comparator.print_summary(report)
        
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            print(f"📄 비교 보고서 저장: {args.report}")
        
        return
    
    # 지정 폴더에 검수 폴더 생성하여 처리
    if args.process_to_review:
        print("🚀 검수 폴더 생성 및 자동 수정 시작")
        
        # 검수 폴더 생성
        review_dir = target_path / "검수"
        review_dir.mkdir(exist_ok=True)
        print(f"📁 검수 폴더 생성: {review_dir}")
        
        # 1. ZIP 파일 추출
        processor = ZipProcessor()
        json_files = processor.process_directory(target_path)
        
        if not json_files:
            print("❌ JSON 파일을 찾을 수 없습니다.")
            sys.exit(1)
        
        # 2. 자동 수정
        print(f"\n🔧 자동 수정 시작: {len(json_files)}개 파일")
        total_fixes = 0
        
        for json_file in json_files:
            if "visualinfo" in json_file.name:
                extract_dir = json_file.parent.parent
                fixer = RuleBasedFixer(extract_dir)
                fixes = fixer.run_all_rule_fixes()
                
                fix_count = sum(len(fix_list) for fix_list in fixes.values())
                if fix_count > 0:
                    fixer.save_fixes()
                    total_fixes += fix_count
                    print(f"  ✅ {json_file.parent.parent.name}: {fix_count}개 수정")
                else:
                    print(f"  📝 {json_file.parent.parent.name}: 수정할 항목 없음")
        
        print(f"\n📊 총 수정 항목: {total_fixes}개")
        
        # 3. 검수 폴더에 재압축
        if total_fixes > 0:
            print(f"\n📦 검수 폴더에 재압축 중...")
            recompressor = ZipRecompressor(review_dir)
            recompressed_files = recompressor.recompress_all(Path("extracted_data"))
            
            print(f"✅ 처리 완료!")
            print(f"📁 수정된 파일 저장 위치: {review_dir}")
            print(f"📦 생성된 파일: {len(recompressed_files)}개")
            
            # 파일명에서 _fixed 제거하여 원본 이름으로 변경
            for zip_file in recompressed_files:
                original_name = zip_file.name.replace("_fixed.zip", ".zip")
                new_path = zip_file.parent / original_name
                
                # 기존 파일이 있으면 삭제
                if new_path.exists():
                    new_path.unlink()
                
                zip_file.rename(new_path)
                print(f"  📄 {original_name}")
        else:
            print("📝 수정된 항목이 없어 재압축을 건너뜁니다.")
        
        return
    
    # 전체 워크플로우 모드 (추출 → 자동수정 → 재압축)
    if args.full_workflow:
        print("🚀 전체 워크플로우 시작: 추출 → 자동수정 → 재압축")
        
        # 1. ZIP 파일 추출
        processor = ZipProcessor()
        json_files = processor.process_directory(target_path)
        
        if not json_files:
            print("❌ JSON 파일을 찾을 수 없습니다.")
            sys.exit(1)
        
        # 2. 자동 수정
        print(f"\n🔧 자동 수정 시작: {len(json_files)}개 파일")
        total_fixes = 0
        
        for json_file in json_files:
            if "visualinfo" in json_file.name:
                extract_dir = json_file.parent.parent
                fixer = RuleBasedFixer(extract_dir)
                fixes = fixer.run_all_rule_fixes()
                
                fix_count = sum(len(fix_list) for fix_list in fixes.values())
                if fix_count > 0:
                    fixer.save_fixes()
                    total_fixes += fix_count
                    print(f"  ✅ {json_file.parent.parent.name}: {fix_count}개 수정")
                else:
                    print(f"  📝 {json_file.parent.parent.name}: 수정할 항목 없음")
        
        print(f"\n📊 총 수정 항목: {total_fixes}개")
        
        # 3. 재압축
        if total_fixes > 0:
            print(f"\n📦 재압축 시작...")
            recompressor = ZipRecompressor()
            recompressed_files = recompressor.recompress_all(Path("extracted_data"))
            
            print(f"✅ 워크플로우 완료!")
            print(f"📁 수정된 파일 저장 위치: {recompressor.output_dir}")
        else:
            print("📝 수정된 항목이 없어 재압축을 건너뜁니다.")
        
        return
    
    # 자동 수정만 실행
    if args.auto_fix:
        processor = ZipProcessor()
        json_files = processor.process_directory(target_path)
        
        if not json_files:
            print("❌ JSON 파일을 찾을 수 없습니다.")
            sys.exit(1)
        
        print(f"🔧 자동 수정 시작: {len(json_files)}개 파일")
        total_fixes = 0
        
        for json_file in json_files:
            if "visualinfo" in json_file.name:
                extract_dir = json_file.parent.parent
                fixer = RuleBasedFixer(extract_dir)
                fixes = fixer.run_all_rule_fixes()
                
                fix_count = sum(len(fix_list) for fix_list in fixes.values())
                if fix_count > 0:
                    fixer.save_fixes()
                    total_fixes += fix_count
                    print(f"  ✅ {json_file.parent.parent.name}: {fix_count}개 수정")
                else:
                    print(f"  📝 {json_file.parent.parent.name}: 수정할 항목 없음")
        
        print(f"\n📊 총 수정 항목: {total_fixes}개")
        return
    
    # 재압축만 실행
    if args.recompress:
        print("📦 재압축 시작...")
        recompressor = ZipRecompressor()
        recompressed_files = recompressor.recompress_all(Path("extracted_data"))
        
        print(f"✅ 재압축 완료!")
        print(f"📁 압축 파일 저장 위치: {recompressor.output_dir}")
        return
    
    start_time = time.time()
    
    try:
        if target_path.is_file():
            print(f"📄 파일 검수: {target_path}")
            issues = controller.validate_file(target_path)
            
            if args.fix and issues:
                print("🔧 자동 수정 실행 중...")
                fixed_issues = controller.auto_fix_file(target_path)
                print(f"✅ 수정 완료: {len(issues) - len(fixed_issues)}개 이슈 해결")
            
        else:
            print(f"📁 디렉토리 검수: {target_path}")
            all_issues = controller.validate_directory(target_path)
            
            if args.fix and all_issues:
                print("🔧 일괄 자동 수정 실행 중...")
                for file_path in all_issues.keys():
                    controller.auto_fix_file(Path(file_path))
                print("✅ 일괄 수정 완료")
            
            # 보고서 생성
            processing_time = time.time() - start_time
            report = controller.generate_report(all_issues, processing_time)
            
            print(f"\n📊 검수 결과:")
            print(f"  총 파일: {report.total_files}개")
            print(f"  총 이슈: {report.total_issues}개")
            print(f"  처리 시간: {report.processing_time:.2f}초")
            
            if args.report:
                controller.export_report(report, Path(args.report))
                print(f"📄 보고서 저장: {args.report}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
