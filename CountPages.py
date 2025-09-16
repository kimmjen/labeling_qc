#!/usr/bin/env python3
"""
CountPages - ZIP 파일들의 페이지 수 분석 도구
"""

import argparse
import json
import sys
import time
import shutil
from pathlib import Path
import PyPDF2
from tqdm import tqdm
import zipfile


def safe_rmtree(path, max_attempts=3, delay=0.5):
    """
    안전한 폴더 삭제 함수 - 권한 오류 시 재시도
    """
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


class ZipProcessor:
    """ZIP 파일 처리 클래스"""
    
    def __init__(self, extract_base_dir=None):
        self.extract_base_dir = extract_base_dir or Path("temp_extract")
    
    def process_directory(self, target_path):
        """디렉토리 내의 ZIP 파일들을 추출하고 JSON 파일 경로 반환"""
        zip_files = list(target_path.glob("*.zip"))
        if not zip_files:
            return []
        
        json_files = []
        
        for zip_file in zip_files:
            try:
                # ZIP 파일명에서 확장자 제거한 폴더명 생성
                folder_name = zip_file.stem
                extract_dir = self.extract_base_dir / folder_name
                
                # 기존 추출 폴더가 있으면 삭제
                if extract_dir.exists():
                    safe_rmtree(extract_dir)
                
                extract_dir.mkdir(parents=True, exist_ok=True)
                
                # ZIP 파일 추출
                with zipfile.ZipFile(zip_file, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # JSON 파일 찾기
                for json_file in extract_dir.rglob("*.json"):
                    if "visualinfo" in json_file.name:
                        json_files.append(json_file)
                        break
                        
            except Exception as e:
                print(f"⚠️ {zip_file.name} 추출 중 오류: {e}")
        
        return json_files


class CountPages:
    def __init__(self, input_path):
        self.input_path = Path(input_path)
    
    def count_pdf_pages(self, pdf_path):
        """PDF 파일의 페이지 수 계산"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                return len(pdf_reader.pages)
        except Exception as e:
            print(f"⚠️ {pdf_path.name} PDF 읽기 오류: {e}")
            return 1  # 실패시 1페이지로 추정
    
    def analyze_single_zip(self, zip_path):
        """단일 ZIP 파일의 페이지 수 분석"""
        temp_extract_dir = zip_path.parent / "temp_page_count"
        
        try:
            # ZIP 파일 추출
            processor = ZipProcessor(extract_base_dir=temp_extract_dir)
            json_files = processor.process_directory(zip_path.parent)
            
            if not json_files:
                print("❌ JSON 파일을 찾을 수 없습니다.")
                return None
            
            # ZIP 파일의 추출된 폴더에서 PDF 파일 찾기
            zip_name = zip_path.stem
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
                    pdf_file = pdf_files[0]
                    pages_count = self.count_pdf_pages(pdf_file)
                    return {doc_name: pages_count}
            
            # original 폴더가 없으면 추정
            print(f"⚠️ {doc_name}: original 폴더에 PDF 파일이 없습니다")
            return {doc_name: 1}
            
        except Exception as e:
            print(f"❌ {zip_path.name} 분석 중 오류: {e}")
            return None
        finally:
            # 임시 디렉토리 정리
            safe_rmtree(temp_extract_dir)
    
    def analyze_directory(self, target_dir):
        """디렉토리 내 모든 ZIP 파일의 페이지 수 분석"""
        print("📊 페이지 수 분석 시작")
        
        # 임시 추출 디렉토리 생성
        temp_extract_dir = target_dir / "temp_page_count"
        temp_extract_dir.mkdir(exist_ok=True)
        
        try:
            # ZIP 파일 추출
            processor = ZipProcessor(extract_base_dir=temp_extract_dir)
            json_files = processor.process_directory(target_dir)

            if not json_files:
                print("❌ JSON 파일을 찾을 수 없습니다.")
                return None

            # 페이지 수 계산 - PDF 파일 기반으로 정확히 계산
            total_pages = 0
            file_pages = {}
            zip_files = list(target_dir.glob("*.zip"))
            
            print(f"\n📂 분석 대상: {len(zip_files)}개 ZIP 파일")
            
            # 각 ZIP 파일의 추출된 폴더에서 PDF 파일 찾기
            with tqdm(total=len(zip_files), desc="📊 페이지 분석", unit="파일") as pbar:
                for zip_file in zip_files:
                    pbar.set_postfix_str(zip_file.name)
                    
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
                            pages_count = self.count_pdf_pages(pdf_file)
                            file_pages[doc_name] = pages_count
                            total_pages += pages_count
                        else:
                            pbar.write(f"⚠️ {doc_name}: original 폴더에 PDF 파일이 없습니다")
                            file_pages[doc_name] = 1
                            total_pages += 1
                    else:
                        pbar.write(f"⚠️ {doc_name}: original 폴더를 찾을 수 없습니다")
                        file_pages[doc_name] = 1
                        total_pages += 1
                    
                    pbar.update(1)

            return {
                "total_documents": len(file_pages),
                "total_pages": total_pages,
                "average_pages": round(total_pages/len(file_pages), 1) if file_pages else 0,
                "documents": file_pages
            }
            
        finally:
            # 임시 디렉토리 정리
            safe_rmtree(temp_extract_dir)
    
    def print_results(self, results):
        """결과 출력"""
        if not results:
            return
        
        if "documents" in results:
            # 디렉토리 분석 결과
            print(f"\n📊 페이지 수 분석 결과:")
            print(f"=" * 50)
            
            for file_name, pages in sorted(results["documents"].items()):
                print(f"📄 {file_name}: {pages}페이지")
            
            print(f"=" * 50)
            print(f"📚 총 {results['total_documents']}개 문서")
            print(f"📖 총 페이지 수: {results['total_pages']}페이지")
            print(f"📊 평균 페이지 수: {results['average_pages']}페이지")
        else:
            # 단일 파일 분석 결과
            for file_name, pages in results.items():
                print(f"\n📊 분석 결과:")
                print(f"📄 {file_name}: {pages}페이지")
    
    def save_report(self, results, report_path):
        """결과를 JSON 파일로 저장"""
        if not results:
            return
        
        if "documents" not in results:
            # 단일 파일 결과를 디렉토리 형식으로 변환
            file_name, pages = list(results.items())[0]
            results = {
                "total_documents": 1,
                "total_pages": pages,
                "average_pages": pages,
                "documents": results
            }
        
        report_data = {
            "analysis_date": time.strftime("%Y-%m-%d %H:%M:%S"),
            **results
        }
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, ensure_ascii=False, indent=2)
        print(f"📄 페이지 수 보고서 저장: {report_path}")
    
    def run(self, report_path=None):
        """메인 실행 함수"""
        print("📊 페이지 수 분석 도구")
        print(f"📂 입력: {self.input_path}")
        
        if self.input_path.is_file() and self.input_path.suffix.lower() == '.zip':
            # 단일 ZIP 파일 분석
            print(f"📄 단일 ZIP 파일 분석 모드")
            results = self.analyze_single_zip(self.input_path)
        elif self.input_path.is_dir():
            # 디렉토리 분석
            print(f"📁 디렉토리 분석 모드")
            results = self.analyze_directory(self.input_path)
        else:
            print("❌ 입력이 ZIP 파일이나 폴더가 아닙니다.")
            return False
        
        if results:
            self.print_results(results)
            
            if report_path:
                self.save_report(results, report_path)
            
            return True
        else:
            print("❌ 분석 실패")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="ZIP 파일들의 페이지 수 분석 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 단일 ZIP 파일 분석
  python CountPages.py file.zip
  
  # 폴더 내 모든 ZIP 파일 분석
  python CountPages.py /path/to/folder
  
  # 결과를 JSON 파일로 저장
  python CountPages.py /path/to/folder --report result.json

기능:
  - PDF 파일 기반 정확한 페이지 수 계산
  - 통계 정보 제공 (총 문서 수, 총 페이지 수, 평균 페이지 수)
  - JSON 형식 보고서 저장
        """
    )
    
    parser.add_argument(
        "input_path", 
        help="분석할 ZIP 파일 또는 폴더 경로"
    )
    
    parser.add_argument(
        "--report", "-r",
        metavar="보고서파일.json",
        help="페이지 수 분석 결과를 JSON 보고서로 저장할 경로"
    )
    
    args = parser.parse_args()
    
    # 경로 검증
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {input_path}")
        sys.exit(1)
    
    # 분석 실행
    counter = CountPages(input_path)
    success = counter.run(report_path=args.report)
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
