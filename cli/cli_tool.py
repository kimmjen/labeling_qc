#!/usr/bin/env python3
"""
CLI 도구 - 품질 검수 명령행 인터페이스
"""

import argparse
import sys
import time
import json
import re
import os
from pathlib import Path
import PyPDF2
from tqdm import tqdm
import shutil
import zipfile

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.quality_controller import QualityController
from src.utils.quality_comparator import QualityComparator
from src.utils.zip_processor import ZipProcessor
from src.utils.zip_recompressor import ZipRecompressor
from src.core.rule_fixer import RuleBasedFixer
from src.services.pdf_uploader import PDFUploader


def safe_rmtree(path, max_attempts=3, delay=0.5):
    """
    안전한 폴더 삭제 함수 - 권한 오류 시 재시도
    """
    from pathlib import Path
    import time
    
    path = Path(path)
    if not path.exists():
        return True
        
    for attempt in range(max_attempts):
        try:
            shutil.rmtree(path)
            return True
        except PermissionError:
            if attempt < max_attempts - 1:
                time.sleep(delay)
            else:
                print(f"⚠️ 폴더 삭제 실패 (권한 오류): {path}")
                return False
        except Exception as e:
            print(f"⚠️ 폴더 삭제 중 오류: {e}")
            return False
    return False


def main():
    """메인 실행 함수"""
    parser = argparse.ArgumentParser(
        description="""
📋 라벨링 품질 검수 도구 v2.0

이 도구는 라벨링 데이터의 품질을 검증하고 자동으로 수정하는 CLI 도구입니다.
JSON 파일 내의 라벨링 오류를 감지하고, 한글 인코딩 문제까지 포함하여 종합적인 품질 관리를 제공합니다.

🔍 지원되는 검증 규칙:
  R001: 원문/번역문이 ListText인 경우 → ParaText로 변경
  R002: 숫자나 □가 없는 RegionTitle → ParaTitle로 변경  
  R003: 법령 구조 라벨링 (제~편/장/절/조, ~법 → ParaTitle)
  R004: 한글 인코딩 오류 검출 (깨진 텍스트, 잘못된 영어 인식)

💡 사용 예시:
  # 단순 검증만 실행
  python cli/cli_tool.py "data/" --validate
  
  # 자동 수정 실행
  python cli/cli_tool.py "data/" --auto-fix
  
  # 검수 폴더 생성하여 전체 워크플로우 실행
  python cli/cli_tool.py "원본폴더/" --process-to-review
  
  # 모든 라벨을 ListText로 통일 후 R003 법령 구조만 적용
  python cli/cli_tool.py "zip폴더/" --listtext-only
  
  # 두 폴더 비교 분석
  python cli/cli_tool.py "원본/" --compare "검수완료/"
  
  # 전체 워크플로우 (추출→수정→재압축)
  python cli/cli_tool.py "data/" --full-workflow
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
📚 상세 옵션 설명:

💼 기본 작업 모드:
  --validate (-v)     : 품질 검증만 실행하고 결과 출력
  --auto-fix          : 검증 후 자동 수정까지 실행
  --process-to-review : 검수 폴더 생성하여 수정된 파일 저장 (권장)

🔧 고급 옵션:
  --full-workflow     : ZIP 추출 → 수정 → 재압축 전체 과정
  --recompress        : 수정 후 ZIP 파일로 재압축
  --compare (-c)      : 두 폴더의 검수 결과 비교

📊 출력 옵션:
  --report (-r)       : 결과를 JSON 파일로 저장
  --verbose           : 상세한 처리 과정 출력

🚀 권장 사용법:
  1. 품질 확인: python cli/cli_tool.py "폴더경로/" --validate
  2. 자동 수정: python cli/cli_tool.py "폴더경로/" --process-to-review
  3. 결과 비교: python cli/cli_tool.py "원본/" --compare "수정본/"

⚠️  주의사항:
  - 원본 파일 백업을 권장합니다
  - --process-to-review 옵션이 가장 안전한 방법입니다
  - R004 규칙은 한글 깨짐을 감지하지만 자동 수정하지 않습니다
        """
    )
    
    # 필수 인수
    parser.add_argument(
        "path", 
        help="검수할 파일 또는 디렉토리 경로 (ZIP 파일 포함 폴더 또는 JSON 파일)"
    )
    
    # 작업 모드 옵션
    mode_group = parser.add_argument_group('작업 모드', '검수 작업의 종류를 선택하세요')
    mode_group.add_argument(
        "--validate", "-v", 
        action="store_true", 
        help="품질 검증만 실행 (수정하지 않음)"
    )
    mode_group.add_argument(
        "--auto-fix", 
        action="store_true", 
        help="자동 수정 실행 (원본 파일 직접 수정)"
    )
    mode_group.add_argument(
        "--process-to-review", 
        action="store_true", 
        help="검수 폴더 생성하여 수정된 파일 저장 (권장 방법)"
    )
    mode_group.add_argument(
        "--full-workflow", 
        action="store_true", 
        help="전체 워크플로우: ZIP 추출 → 품질검수 → 자동수정 → 재압축"
    )
    mode_group.add_argument(
        "--listtext-only", 
        action="store_true", 
        help="모든 라벨(ParaText, RegionTitle 등)을 ListText로 통일 후 R003 법령 구조 규칙만 적용"
    )

    mode_group.add_argument(
        "--listtext-only2", 
        action="store_true", 
        help="모든 라벨을 ListText로 통일 후 R003 법령 구조 규칙만 적용 (단일 ZIP 파일 또는 폴더 지원, 폴더 구조 유지)"
    )

    mode_group.add_argument(
        "--paratext-only", 
        action="store_true", 
        help="모든 라벨(ParaText, RegionTitle 등)을 ListText로 통일 후 R003 법령 구조 규칙만 적용"
    )
    mode_group.add_argument(
        "--count-pages", 
        action="store_true", 
        help="ZIP 파일들의 총 페이지 수를 분석하고 통계 정보 출력"
    )
    mode_group.add_argument(
        "--count-pages-by-worker", 
        action="store_true", 
        help="작업자별 폴더의 페이지 수를 분석하고 통합 보고서 생성"
    )
    mode_group.add_argument(
        "--upload", 
        action="store_true", 
        help="PDF 파일들을 API로 업로드하여 OCR 처리 후 visualcontent ZIP 파일로 저장"
    )
    
    # 비교 및 분석 옵션
    analysis_group = parser.add_argument_group('비교 및 분석', '검수 결과를 비교하고 분석합니다')
    analysis_group.add_argument(
        "--compare", "-c", 
        metavar="완료폴더경로",
        help="검수 완료 폴더와 비교하여 정확도 분석"
    )
    
    # 출력 및 보고서 옵션
    output_group = parser.add_argument_group('출력 및 보고서', '결과 저장 및 출력 방식을 설정합니다')
    output_group.add_argument(
        "--report", "-r", 
        metavar="보고서파일.json",
        help="검수 결과를 JSON 보고서로 저장할 경로"
    )
    output_group.add_argument(
        "--verbose", 
        action="store_true", 
        help="상세한 처리 과정과 디버그 정보 출력"
    )
    
    # 고급 옵션 (하위 호환성)
    advanced_group = parser.add_argument_group('고급 옵션', '특수한 용도로 사용되는 옵션들')
    advanced_group.add_argument(
        "--fix", "-f", 
        action="store_true", 
        help="자동 수정 실행 (--auto-fix와 동일, 하위 호환성용)"
    )
    advanced_group.add_argument(
        "--recompress", 
        action="store_true", 
        help="수정 후 ZIP 파일로 재압축"
    )
    
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
    
    # 작업자별 페이지 수 계산 모드
    if args.count_pages_by_worker:
        print("📊 작업자별 페이지 수 분석 시작")
        print(f"🎯 대상 폴더: {target_path}")
        
        # 폴더 내용 먼저 확인
        print(f"📂 폴더 내용 스캔...")
        for item in target_path.iterdir():
            if item.is_dir():
                zip_count = len(list(item.glob("*.zip")))
                print(f"   📁 {item.name}/ (ZIP: {zip_count}개)")
            elif item.is_file():
                print(f"   📄 {item.name} ({item.suffix})")
        
        # 작업자별 폴더 스캔
        worker_folders = []
        for item in target_path.iterdir():
            if item.is_dir() and not item.name.startswith('.') and item.name not in ['temp_page_count', 'temp_extract']:
                # 폴더 내 ZIP 파일 확인
                zip_files = list(item.glob("*.zip"))
                if zip_files:
                    worker_folders.append(item)
                    print(f"   ✅ 작업자 폴더 인식: {item.name}")
            elif item.is_file() and item.suffix.lower() == '.zip':
                # 작업자별 통합 ZIP 파일인 경우 (파일명이 작업자명)
                worker_folders.append(item)
                print(f"   ✅ 작업자 ZIP 파일 인식: {item.name}")
        
        if not worker_folders:
            print("❌ 작업자 폴더 또는 작업자별 ZIP 파일을 찾을 수 없습니다.")
            print("💡 확인 사항:")
            print("   - 폴더 내에 ZIP 파일이 있는 하위 폴더가 있는지")
            print("   - 작업자명.zip 형태의 파일이 있는지")
            sys.exit(1)
        
        print(f"👥 발견된 작업자: {len(worker_folders)}명")
        for worker_item in worker_folders:
            if worker_item.is_dir():
                zip_count = len(list(worker_item.glob("*.zip")))
                print(f"   📁 {worker_item.name}: {zip_count}개 ZIP 파일")
            else:
                print(f"   📦 {worker_item.stem}: 통합 ZIP 파일")
        
        # 전체 결과 저장용
        all_results = {
            "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_workers": len(worker_folders),
            "workers": {},
            "summary": {}
        }
        
        total_documents = 0
        total_pages = 0
        
        # 각 작업자별 분석
        for worker_item in worker_folders:
            if worker_item.is_dir():
                worker_name = worker_item.name
                worker_zip_source = worker_item  # 폴더 내 ZIP 파일들
            else:
                worker_name = worker_item.stem
                worker_zip_source = worker_item  # 통합 ZIP 파일
            
            print(f"\n👤 {worker_name} 분석 중...")
            
            try:
                # 페이지 수 계산
                worker_total_pages = 0
                worker_file_pages = {}
                
                if worker_item.is_dir():
                    # 폴더 내 ZIP 파일들 처리 (통합 ZIP)
                    worker_zip_files = list(worker_zip_source.glob("*.zip"))
                    print(f"   📁 폴더에서 {len(worker_zip_files)}개 통합 ZIP 파일 발견")
                    
                    # 모든 개별 ZIP 파일을 저장할 리스트
                    zip_files = []
                    
                    # 각 통합 ZIP 파일을 처리
                    for unified_zip in worker_zip_files:
                        print(f"   📦 통합 ZIP 해제: {unified_zip.name}")
                        
                        # 통합 ZIP을 작업자 폴더에 직접 해제
                        unified_extract_dir = worker_zip_source / f"extracted_{unified_zip.stem}"
                        unified_extract_dir.mkdir(exist_ok=True)
                        
                        print(f"      📁 해제 위치: {unified_extract_dir}")
                        
                        try:
                            with zipfile.ZipFile(unified_zip, 'r') as zip_ref:
                                file_list = zip_ref.namelist()
                                individual_zips = [f for f in file_list if f.endswith('.zip')]
                                print(f"      📦 내부에서 {len(individual_zips)}개 개별 ZIP 발견")
                                
                                # 통합 ZIP 압축 해제 (작업자 폴더에 직접)
                                zip_ref.extractall(unified_extract_dir)
                                print(f"      ✅ 해제 완료: {len(file_list)}개 파일")
                                
                                # 개별 ZIP 파일들을 리스트에 추가
                                for zip_name in individual_zips:
                                    zip_path = unified_extract_dir / zip_name
                                    if zip_path.exists():
                                        zip_files.append(zip_path)
                                        if worker_name in ['강아름', '김경진']:
                                            print(f"         ✅ 개별 ZIP: {zip_name}")
                                
                        except Exception as e:
                            print(f"      ❌ 통합 ZIP 해제 오류: {e}")
                            continue
                    
                    print(f"   📊 총 {len(zip_files)}개 개별 ZIP 파일 처리 예정")
                else:
                    # 통합 ZIP 파일 먼저 압축 해제
                    print(f"   📦 통합 ZIP 파일 압축 해제 중... ({worker_zip_source})")
                    print(f"   📦 파일 크기: {worker_zip_source.stat().st_size:,} bytes")
                    
                    worker_extract_dir = temp_extract_dir / "worker_extracted"
                    worker_extract_dir.mkdir(exist_ok=True)
                    
                    try:
                        with zipfile.ZipFile(worker_zip_source, 'r') as zip_ref:
                            # ZIP 파일 내용 확인
                            file_list = zip_ref.namelist()
                            print(f"   📦 ZIP 내부 파일 {len(file_list)}개 발견")
                            if len(file_list) <= 10:
                                for f in file_list[:10]:
                                    print(f"      - {f}")
                            else:
                                for f in file_list[:5]:
                                    print(f"      - {f}")
                                print(f"      ... (총 {len(file_list)}개)")
                            
                            # 압축 해제
                            zip_ref.extractall(worker_extract_dir)
                            print(f"   ✅ 압축 해제 완료: {worker_extract_dir}")
                            
                    except zipfile.BadZipFile as e:
                        print(f"   ❌ 잘못된 ZIP 파일: {e}")
                        continue
                    except Exception as e:
                        print(f"   ❌ 압축 해제 오류: {e}")
                        continue
                    
                    # 압축 해제된 폴더에서 개별 ZIP 파일들 찾기
                    zip_files = []
                    print(f"   🔍 개별 ZIP 파일 검색 중...")
                    
                    for root, dirs, files in os.walk(worker_extract_dir):
                        print(f"      📂 검색 중: {root}")
                        zip_in_dir = [f for f in files if f.endswith('.zip')]
                        if zip_in_dir:
                            print(f"         찾은 ZIP: {zip_in_dir}")
                        for file in files:
                            if file.endswith('.zip'):
                                zip_path = Path(root) / file
                                zip_files.append(zip_path)
                                print(f"         ✅ 발견: {zip_path}")
                    
                    print(f"   📦 통합 ZIP에서 {len(zip_files)}개 개별 ZIP 파일 발견")
                
                # 개별 ZIP 파일들 분석 (ZipProcessor 사용하지 않음)
                for zip_file in zip_files:
                    zip_name = zip_file.stem
                    if zip_name.startswith('visualcontent-'):
                        doc_name = zip_name.replace('visualcontent-', '')
                    else:
                        doc_name = zip_name
                    
                    try:
                        # 개별 ZIP 파일을 작업자 폴더 내에 압축 해제
                        # 파일명에서 .zip 제거하고 폴더명으로 사용
                        zip_extract_dir = zip_file.parent / f"doc_{doc_name}"
                        zip_extract_dir.mkdir(exist_ok=True)
                        
                        with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                            zip_ref.extractall(zip_extract_dir)
                        
                        # original 폴더의 PDF 파일 찾기
                        original_folder = zip_extract_dir / "original"
                        
                        if worker_name in ['강아름', '김경진']:  # 처음 2명만 상세 로그
                            print(f"      📄 {doc_name} 분석:")
                            print(f"         ZIP 압축 해제: {zip_extract_dir}")
                            print(f"         original 폴더 존재: {original_folder.exists()}")
                        
                        if original_folder.exists():
                            pdf_files = list(original_folder.glob("*.pdf"))
                            if worker_name in ['강아름', '김경진']:
                                print(f"         PDF 파일: {[f.name for f in pdf_files]}")
                            
                            if pdf_files:
                                pdf_file = pdf_files[0]
                                try:
                                    with open(pdf_file, 'rb') as file:
                                        pdf_reader = PyPDF2.PdfReader(file)
                                        pages_count = len(pdf_reader.pages)
                                    
                                    if worker_name in ['강아름', '김경진']:
                                        print(f"         PDF 페이지 수: {pages_count}페이지")
                                        print(f"         PDF 파일 크기: {pdf_file.stat().st_size:,} bytes")
                                    
                                    worker_file_pages[doc_name] = pages_count
                                    worker_total_pages += pages_count
                                    
                                except Exception as e:
                                    if worker_name in ['강아름', '김경진']:
                                        print(f"         ❌ PDF 읽기 오류: {e}")
                                    worker_file_pages[doc_name] = 1
                                    worker_total_pages += 1
                            else:
                                if worker_name in ['강아름', '김경진']:
                                    print(f"         ⚠️ PDF 파일 없음 - 기본값 1페이지 적용")
                                worker_file_pages[doc_name] = 1
                                worker_total_pages += 1
                        else:
                            if worker_name in ['강아름', '김경진']:
                                print(f"         ⚠️ original 폴더 없음 - 기본값 1페이지 적용")
                            worker_file_pages[doc_name] = 1
                            worker_total_pages += 1
                            
                    except Exception as e:
                        print(f"⚠️ {zip_file.name} 처리 오류: {e}")
                        worker_file_pages[doc_name] = 1
                        worker_total_pages += 1
                
                # 작업자별 결과 저장
                worker_result = {
                    "documents_count": len(worker_file_pages),
                    "total_pages": worker_total_pages,
                    "average_pages": round(worker_total_pages/len(worker_file_pages), 1) if worker_file_pages else 0,
                    "documents": worker_file_pages
                }
                
                all_results["workers"][worker_name] = worker_result
                total_documents += len(worker_file_pages)
                total_pages += worker_total_pages
                
                # 작업자별 요약 출력
                print(f"   📚 문서 수: {len(worker_file_pages)}개")
                print(f"   📖 총 페이지: {worker_total_pages}페이지")
                print(f"   📊 평균: {worker_total_pages/len(worker_file_pages):.1f}페이지" if worker_file_pages else "   📊 평균: 0페이지")
                
            except Exception as e:
                print(f"❌ {worker_name} 분석 오류: {e}")
                all_results["workers"][worker_name] = {
                    "error": str(e),
                    "documents_count": 0,
                    "total_pages": 0,
                    "average_pages": 0
                }
            
            except Exception as e:
                print(f"❌ {worker_name} 분석 오류: {e}")
                all_results["workers"][worker_name] = {
                    "error": str(e),
                    "documents_count": 0,
                    "total_pages": 0,
                    "average_pages": 0
                }
        
        # 전체 요약 계산
        all_results["summary"] = {
            "total_documents": total_documents,
            "total_pages": total_pages,
            "average_pages_per_document": round(total_pages/total_documents, 1) if total_documents else 0,
            "average_documents_per_worker": round(total_documents/len(worker_folders), 1),
            "average_pages_per_worker": round(total_pages/len(worker_folders), 1)
        }
        
        # 전체 결과 출력
        print(f"\n" + "="*60)
        print(f"📊 작업자별 페이지 수 분석 완료")
        print(f"="*60)
        
        for worker_name, result in all_results["workers"].items():
            if "error" not in result:
                print(f"👤 {worker_name:12} | 📚 {result['documents_count']:3}개 | 📖 {result['total_pages']:4}페이지 | 📊 평균 {result['average_pages']:4.1f}페이지")
            else:
                print(f"👤 {worker_name:12} | ❌ 오류 발생")
        
        print(f"="*60)
        print(f"📈 전체 요약:")
        print(f"   👥 총 작업자: {len(worker_folders)}명")
        print(f"   📚 총 문서: {total_documents}개")
        print(f"   📖 총 페이지: {total_pages}페이지")
        print(f"   📊 문서당 평균: {all_results['summary']['average_pages_per_document']}페이지")
        print(f"   📊 작업자당 평균 문서: {all_results['summary']['average_documents_per_worker']}개")
        print(f"   📊 작업자당 평균 페이지: {all_results['summary']['average_pages_per_worker']}페이지")
        
        # 보고서 저장
        if args.report:
            with open(args.report, 'w', encoding='utf-8') as f:
                json.dump(all_results, f, ensure_ascii=False, indent=2)
            print(f"\n📄 작업자별 분석 보고서 저장: {args.report}")
        
        return
    
    # 페이지 수 계산 모드
    if args.count_pages:
        print("📊 페이지 수 분석 시작")
        
        # 임시 추출 디렉토리 생성
        temp_extract_dir = target_path / "temp_page_count"
        temp_extract_dir.mkdir(exist_ok=True)
        
        try:
            # ZIP 파일 추출
            processor = ZipProcessor(extract_base_dir=temp_extract_dir)
            json_files = processor.process_directory(target_path)

            if not json_files:
                print("❌ JSON 파일을 찾을 수 없습니다.")
                shutil.rmtree(temp_extract_dir, ignore_errors=True)
                sys.exit(1)

            # 페이지 수 계산 - PDF 파일 기반으로 정확히 계산
            total_pages = 0
            file_pages = {}
            zip_files = list(target_path.glob("*.zip"))
            
            print(f"\n📂 분석 대상: {len(zip_files)}개 ZIP 파일")
            
            # 각 ZIP 파일의 추출된 폴더에서 PDF 파일 찾기
            for zip_file in zip_files:
                zip_name = zip_file.stem
                if zip_name.startswith('visualcontent-'):
                    doc_name = zip_name.replace('visualcontent-', '')
                else:
                    doc_name = zip_name
                
                # 추출된 폴더에서 original 폴더의 PDF 파일 찾기
                extracted_folder = temp_extract_dir / zip_name
                original_folder = extracted_folder / "original"
                
                if original_folder.exists():
                    pdf_files = list(original_folder.glob("*.pdf"))
                    if pdf_files:
                        pdf_file = pdf_files[0]  # 첫 번째 PDF 파일 사용
                        try:
                            # PDF 파일의 페이지 수 읽기
                            with open(pdf_file, 'rb') as file:
                                pdf_reader = PyPDF2.PdfReader(file)
                                pages_count = len(pdf_reader.pages)
                                
                            file_pages[doc_name] = pages_count
                            total_pages += pages_count
                            
                        except Exception as e:
                            print(f"⚠️ {pdf_file.name} PDF 읽기 오류: {e}")
                            # PDF 읽기 실패시 JSON 기반으로 추정
                            file_pages[doc_name] = 1
                            total_pages += 1
                    else:
                        print(f"⚠️ {doc_name}: original 폴더에 PDF 파일이 없습니다")
                        file_pages[doc_name] = 1
                        total_pages += 1
                else:
                    print(f"⚠️ {doc_name}: original 폴더를 찾을 수 없습니다")
                    file_pages[doc_name] = 1
                    total_pages += 1

            # 결과 출력
            print(f"\n📊 페이지 수 분석 결과:")
            print(f"=" * 50)
            
            for file_name, pages in sorted(file_pages.items()):
                print(f"📄 {file_name}: {pages}페이지")
            
            print(f"=" * 50)
            print(f"📚 총 {len(file_pages)}개 문서")
            print(f"📖 총 페이지 수: {total_pages}페이지")
            print(f"📊 평균 페이지 수: {total_pages/len(file_pages):.1f}페이지" if file_pages else "📊 평균: 0페이지")
            
            # 보고서 저장
            if args.report:
                page_report = {
                    "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
                    "total_documents": len(file_pages),
                    "total_pages": total_pages,
                    "average_pages": round(total_pages/len(file_pages), 1) if file_pages else 0,
                    "documents": file_pages
                }
                
                with open(args.report, 'w', encoding='utf-8') as f:
                    json.dump(page_report, f, ensure_ascii=False, indent=2)
                print(f"📄 페이지 수 보고서 저장: {args.report}")
        
        finally:
            # 임시 디렉토리 정리
            shutil.rmtree(temp_extract_dir, ignore_errors=True)
        
        return
    
    # PDF 업로드 및 OCR 처리 모드
    if args.upload:
        print("📤 PDF 업로드 및 OCR 처리 시작")
        
        # PDF 파일 검색
        pdf_files = list(target_path.glob("*.pdf")) + list(target_path.glob("*.PDF"))
        
        if not pdf_files:
            print("❌ PDF 파일을 찾을 수 없습니다.")
            sys.exit(1)
        
        print(f"📂 발견된 PDF 파일: {len(pdf_files)}개")
        
        # PDF 업로드 처리기 초기화
        uploader = PDFUploader()
        
        success_count = 0
        start_time = time.time()
        
        # tqdm으로 진행률 표시
        with tqdm(total=len(pdf_files), desc="📤 PDF 처리 중", 
                  unit="파일", bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]") as pbar:
            
            for pdf_file in pdf_files:
                file_start_time = time.time()
                pbar.set_postfix_str(f"현재: {pdf_file.name}")
                
                try:
                    # 1. PDF 업로드
                    pbar.set_description("📤 업로드 중")
                    file_info = uploader.upload_pdf(pdf_file)
                    if not file_info:
                        pbar.write(f"❌ 업로드 실패: {pdf_file.name}")
                        pbar.update(1)
                        continue
                    
                    upload_time = time.time() - file_start_time
                    pbar.write(f"✅ 업로드 완료: {file_info['fileName']} ({file_info['numOfPages']}페이지, {upload_time:.1f}초)")
                    
                    # 2. OCR 처리 요청
                    pbar.set_description("🔍 OCR 요청 중")
                    ocr_start_time = time.time()
                    extract_result = uploader.extract_pages(file_info['fileId'], f"1-{file_info['numOfPages']}")
                    if not extract_result:
                        pbar.write(f"❌ OCR 처리 실패: {pdf_file.name}")
                        pbar.update(1)
                        continue
                    
                    ocr_request_time = time.time() - ocr_start_time
                    pbar.write(f"🔍 OCR 요청 완료: {pdf_file.name} ({ocr_request_time:.1f}초)")
                    
                    # 3. VisualInfo 다운로드 (대기 시간 포함)
                    pbar.set_description("⏳ OCR 결과 대기")
                    visual_start_time = time.time()
                    visual_info = uploader.get_visual_info(file_info['fileId'], progress_callback=lambda msg: pbar.set_postfix_str(msg))
                    if not visual_info:
                        pbar.write(f"❌ VisualInfo 다운로드 실패: {pdf_file.name}")
                        pbar.update(1)
                        continue
                    
                    visual_time = time.time() - visual_start_time
                    pbar.write(f"📄 VisualInfo 완료: {pdf_file.name} ({visual_time:.1f}초)")
                    
                    # 4. ZIP 파일로 저장
                    pbar.set_description("📦 ZIP 생성 중")
                    zip_start_time = time.time()
                    zip_filename = f"visualcontent-{pdf_file.stem}.zip"
                    zip_path = target_path / zip_filename
                    
                    zip_created = uploader.create_visualcontent_zip(
                        pdf_file, visual_info, zip_path, file_info['fileId']
                    )
                    
                    zip_time = time.time() - zip_start_time
                    file_total_time = time.time() - file_start_time
                    
                    if zip_created:
                        pbar.write(f"📦 ZIP 생성 완료: {zip_filename} (생성: {zip_time:.1f}초, 총: {file_total_time:.1f}초)")
                        success_count += 1
                    else:
                        pbar.write(f"❌ ZIP 파일 생성 실패: {pdf_file.name}")
                    
                except Exception as e:
                    pbar.write(f"❌ {pdf_file.name} 처리 중 오류: {e}")
                finally:
                    pbar.update(1)
        
        total_time = time.time() - start_time
        print(f"\n✅ 업로드 완료: {success_count}/{len(pdf_files)}개 파일")
        print(f"⏱️  총 처리 시간: {total_time:.1f}초 (평균: {total_time/len(pdf_files):.1f}초/파일)")
        return
    
    # ListText 통일 + R003 법령 구조 적용 모드
    if args.listtext_only:
        print("📝 ListText 통일 + R003 법령 구조 적용 시작")
        
        # 검수 폴더 및 내부 extracted_data 폴더 생성 (ZIP 파일이 있는 디렉토리에)
        review_dir = target_path / "검수_ListText"
        review_dir.mkdir(exist_ok=True)
        extracted_dir = review_dir / "extracted_data"
        extracted_dir.mkdir(exist_ok=True)
        print(f"📁 검수 폴더 생성: {review_dir}")
        print(f"📁 추출 폴더 생성: {extracted_dir}")

        # 1. ZIP 파일 추출
        processor = ZipProcessor(extract_base_dir=extracted_dir)
        json_files = processor.process_directory(target_path)

        if not json_files:
            print("❌ JSON 파일을 찾을 수 없습니다.")
            sys.exit(1)

        # 2. ListText 통일 + R003 적용
        print(f"\n🔧 ListText 통일 및 R003 법령 구조 적용: {len(json_files)}개 파일")
        total_changes = 0

        for json_file in json_files:
            if "visualinfo" in json_file.name:
                try:
                    # JSON 파일 로드
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    elements = data.get('elements', [])
                    changes = 0
                    
                    for element in elements:
                        category = element.get('category', {})
                        text = element.get('content', {}).get('text', '').strip()
                        current_label = category.get('label', '')
                        
                        # 1단계: PageNumber를 제외하고 모든 것을 ListText로 변경
                        if current_label != 'ListText' and current_label != 'PageNumber':
                            category['label'] = 'ListText'
                            category['type'] = 'LIST'  # type도 함께 변경
                            changes += 1
                    
                    # 2단계: R003 법령 구조 규칙 적용 (ListText → ParaTitle)
                    for element in elements:
                        category = element.get('category', {})
                        text = element.get('content', {}).get('text', '').strip()
                        current_label = category.get('label', '')
                        
                        if current_label == 'ListText' and text:
                            # ~법 패턴
                            if re.search(r'[가-힣]+법$', text):
                                category['label'] = 'ParaTitle'
                                category['type'] = 'HEADING'  # type도 함께 변경
                                changes += 1
                            # 제~편, 제~장, 제~절, 제~조 패턴
                            elif re.search(r'^제\s*\d+\s*(편|장|절|관|조)', text):
                                category['label'] = 'ParaTitle'
                                category['type'] = 'HEADING'  # type도 함께 변경
                                changes += 1
                    
                    if changes > 0:
                        # JSON 파일 저장
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        
                        total_changes += changes
                        print(f"  ✅ {json_file.parent.parent.name}: {changes}개 변경")
                    else:
                        print(f"  📝 {json_file.parent.parent.name}: 변경할 항목 없음")
                        
                except Exception as e:
                    print(f"  ❌ {json_file.parent.parent.name}: 오류 - {str(e)}")

        print(f"\n📊 총 변경 항목: {total_changes}개")

        # 3. 재압축
        if total_changes > 0:
            print(f"\n📦 재압축 중...")
            recompressor = ZipRecompressor(review_dir)
            recompressed_files = recompressor.recompress_all(extracted_dir)

            print(f"✅ 처리 완료!")
            print(f"📁 수정된 파일 저장 위치: {review_dir}")
            print(f"📦 생성된 파일: {len(recompressed_files)}개")
        else:
            print("📝 변경사항이 없어 재압축하지 않습니다.")

        return
    
    if args.listtext_only2:
        print("📝 ListText 통일 + R003 법령 구조 적용 (폴더 구조 유지)")
        
        # 1. 경로 설정 및 입력 타입 확인
        if target_path.is_file() and target_path.suffix.lower() == '.zip':
            # 단일 ZIP 파일 처리
            output_dir = target_path.parent / f"{target_path.stem}_ListText"
            temp_processing_dir = target_path.parent / "temp_processing_ListText"
            zip_files = [target_path]
            print(f"📄 단일 ZIP 파일 처리 모드")
        else:
            # 폴더 처리 (기존 방식)
            output_dir = target_path.parent / f"{target_path.name}_ListText"
            temp_processing_dir = target_path.parent / "temp_processing_ListText"
            zip_files = list(target_path.rglob("*.zip"))
            print(f"📁 폴더 처리 모드")
        
        # 이전 결과 폴더/임시 폴더 삭제
        if output_dir.exists():
            safe_rmtree(output_dir)
        if temp_processing_dir.exists():
            safe_rmtree(temp_processing_dir)
            
        output_dir.mkdir(exist_ok=True)
        temp_processing_dir.mkdir(exist_ok=True)
        
        print(f"📂 원본 경로: {target_path}")
        print(f"📁 결과물 저장 경로: {output_dir}")
        
        # 2. ZIP 파일 목록 확인
        if not zip_files:
            if target_path.is_file():
                print("❌ 지정된 파일이 ZIP 파일이 아닙니다.")
            else:
                print("❌ 처리할 ZIP 파일을 찾을 수 없습니다.")
            safe_rmtree(temp_processing_dir)
            sys.exit(1)
            
        print(f"� 총 {len(zip_files)}개의 ZIP 파일을 처리합니다.")
        
        total_changes = 0
        
        # 3. 파일 단위 처리
        with tqdm(total=len(zip_files), desc="🚀 전체 진행률", unit="개") as pbar:
            for zip_path in zip_files:
                pbar.set_postfix_str(zip_path.name)
                
                try:
                    # 3-1. 임시 추출
                    extract_dir = temp_processing_dir / zip_path.stem
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                        
                    # 3-2. visualinfo.json 파일 찾기
                    visualinfo_files = list(extract_dir.rglob("*_visualinfo.json"))
                    if not visualinfo_files:
                        pbar.write(f"  ⚠️ {zip_path.name}: visualinfo.json 파일 없음")
                        # 원본 ZIP 그대로 복사
                        relative_path = zip_path.relative_to(target_path)
                        dest_path = output_dir / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(zip_path, dest_path)
                        continue

                    json_file = visualinfo_files[0]
                    
                    # 3-3. ListText 변환 로직
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    elements = data.get('elements', [])
                    changes = 0
                    
                    # 1단계: PageNumber 제외하고 ListText로 변경
                    for element in elements:
                        category = element.get('category', {})
                        if category.get('label') not in ['ListText', 'PageNumber']:
                            category['label'] = 'ListText'
                            category['type'] = 'LIST'
                            changes += 1
                    
                    # 2단계: 법령 구조 규칙 적용
                    for element in elements:
                        category = element.get('category', {})
                        text = element.get('content', {}).get('text', '').strip()
                        if category.get('label') == 'ListText' and text:
                            if re.search(r'[가-힣]+법$', text) or re.search(r'^제\s*\d+\s*(편|장|절|관|조)', text):
                                category['label'] = 'ParaTitle'
                                category['type'] = 'HEADING'
                                changes += 1
                    
                    if changes > 0:
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        total_changes += changes
                        pbar.write(f"  ✅ {zip_path.name}: {changes}개 항목 변경")
                    else:
                        pbar.write(f"  📝 {zip_path.name}: 변경 사항 없음")

                    # 3-4. 결과물 재압축 및 저장
                    relative_path = zip_path.relative_to(target_path)
                    dest_path = output_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        for file_to_zip in extract_dir.rglob('*'):
                            if file_to_zip.is_file():
                                arcname = file_to_zip.relative_to(extract_dir)
                                new_zip.write(file_to_zip, arcname)

                except Exception as e:
                    pbar.write(f"  ❌ {zip_path.name} 처리 중 오류: {e}")
                finally:
                    # 임시 추출 폴더 정리
                    if 'extract_dir' in locals():
                        safe_rmtree(extract_dir)
                    pbar.update(1)

        # 4. 최종 정리
        safe_rmtree(temp_processing_dir)
        print(f"\n🎉 처리 완료! 총 {total_changes}개 항목이 변경되었습니다.")
        print(f"📂 결과는 {output_dir} 폴더에 저장되었습니다.")
        return
    
    if args.paratext_only:
        print("📝 ListText 통일 + R003 법령 구조 적용 (폴더 구조 유지)")
        
        # 1. 경로 설정
        output_dir = target_path.parent / f"{target_path.name}_ListText"
        temp_processing_dir = target_path.parent / "temp_processing_ListText"
        
        # 이전 결과 폴더/임시 폴더 삭제
        if output_dir.exists():
            shutil.rmtree(output_dir)
        if temp_processing_dir.exists():
            shutil.rmtree(temp_processing_dir)
            
        output_dir.mkdir(exist_ok=True)
        temp_processing_dir.mkdir(exist_ok=True)
        
        print(f"� 원본 경로: {target_path}")
        print(f"📁 결과물 저장 경로: {output_dir}")
        
        # 2. ZIP 파일 목록 탐색
        zip_files = list(target_path.rglob("*.zip"))
        if not zip_files:
            print("❌ 처리할 ZIP 파일을 찾을 수 없습니다.")
            shutil.rmtree(temp_processing_dir)
            sys.exit(1)
            
        print(f"� 총 {len(zip_files)}개의 ZIP 파일을 처리합니다.")
        
        total_changes = 0
        
        # 3. 파일 단위 처리
        with tqdm(total=len(zip_files), desc="🚀 전체 진행률", unit="개") as pbar:
            for zip_path in zip_files:
                pbar.set_postfix_str(zip_path.name)
                
                try:
                    # 3-1. 임시 추출
                    extract_dir = temp_processing_dir / zip_path.stem
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                        
                    # 3-2. visualinfo.json 파일 찾기
                    visualinfo_files = list(extract_dir.rglob("*_visualinfo.json"))
                    if not visualinfo_files:
                        pbar.write(f"  ⚠️ {zip_path.name}: visualinfo.json 파일 없음")
                        # 원본 ZIP 그대로 복사
                        relative_path = zip_path.relative_to(target_path)
                        dest_path = output_dir / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(zip_path, dest_path)
                        continue

                    json_file = visualinfo_files[0]
                    
                    # 3-3. ListText 변환 로직
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    elements = data.get('elements', [])
                    changes = 0
                    
                    # 1단계: PageNumber 제외하고 ListText로 변경
                    for element in elements:
                        category = element.get('category', {})
                        if category.get('label') in ['ParaText']:
                            category['label'] = 'ListText'
                            category['type'] = 'LIST'
                            changes += 1
                    
                    # 2단계: 법령 구조 규칙 적용
                    for element in elements:
                        category = element.get('category', {})
                        text = element.get('content', {}).get('text', '').strip()
                        if category.get('label') == 'ListText' and text:
                            if re.search(r'[가-힣]+법$', text) or re.search(r'^제\s*\d+\s*(편|장|절|관|조)', text):
                                category['label'] = 'ParaTitle'
                                category['type'] = 'HEADING'
                                changes += 1
                    
                    if changes > 0:
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        total_changes += changes
                        pbar.write(f"  ✅ {zip_path.name}: {changes}개 항목 변경")
                    else:
                        pbar.write(f"  📝 {zip_path.name}: 변경 사항 없음")

                    # 3-4. 결과물 재압축 및 저장
                    relative_path = zip_path.relative_to(target_path)
                    dest_path = output_dir / relative_path
                    dest_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                        for file_to_zip in extract_dir.rglob('*'):
                            if file_to_zip.is_file():
                                arcname = file_to_zip.relative_to(extract_dir)
                                new_zip.write(file_to_zip, arcname)

                except Exception as e:
                    pbar.write(f"  ❌ {zip_path.name} 처리 중 오류: {e}")
                finally:
                    # 임시 추출 폴더 정리
                    shutil.rmtree(extract_dir, ignore_errors=True)
                    pbar.update(1)

        # 4. 최종 정리
        shutil.rmtree(temp_processing_dir, ignore_errors=True)
        print(f"\n🎉 처리 완료! 총 {total_changes}개 항목이 변경되었습니다.")
        print(f"� 결과는 {output_dir} 폴더에 저장되었습니다.")
        return
    
    # 지정 폴더에 검수 폴더 생성하여 처리
    if args.process_to_review:
        print("🚀 검수 폴더 생성 및 자동 수정 시작")
        
        # 검수 폴더 및 내부 extracted_data 폴더 생성
        review_dir = target_path / "검수"
        review_dir.mkdir(exist_ok=True)
        extracted_dir = review_dir / "extracted_data"
        extracted_dir.mkdir(exist_ok=True)
        print(f"📁 검수 폴더 생성: {review_dir}")
        print(f"📁 추출 폴더 생성: {extracted_dir}")

        # 1. ZIP 파일 추출 (검수폴더 내부 extracted_data에 추출)
        processor = ZipProcessor(extract_base_dir=extracted_dir)
        json_files = processor.process_directory(target_path)

        if not json_files:
            print("❌ JSON 파일을 찾을 수 없습니다.")
            sys.exit(1)

        # 2. 자동 수정 (extracted_dir 내부 파일만 대상으로)
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

        # 3. 검수 폴더에 재압축 (extracted_dir에서 review_dir로)
        if total_fixes > 0:
            print(f"\n📦 검수 폴더에 재압축 중...")
            recompressor = ZipRecompressor(review_dir)
            recompressed_files = recompressor.recompress_all(extracted_dir)

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
