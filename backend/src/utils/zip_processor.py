#!/usr/bin/env python3
"""
ZIP 파일 처리기
라벨링 데이터 ZIP 파일을 추출하고 JSON 파일을 찾는 도구
"""

import zipfile
from pathlib import Path
from typing import List
import shutil


class ZipProcessor:
    """ZIP 파일 처리기"""
    
    def __init__(self, extract_base_dir: Path = None):
        """
        Args:
            extract_base_dir (Path, optional): ZIP 파일을 추출할 기본 디렉토리. None이면 ZIP 파일이 있는 위치에 추출
        """
        self.extract_base_dir = extract_base_dir
    
    def extract_zip_file(self, zip_path: Path) -> Path:
        """ZIP 파일 추출"""
        if self.extract_base_dir:
            # 지정된 기본 디렉토리 아래에 추출
            extract_dir = self.extract_base_dir / zip_path.stem
        else:
            # 원본 위치에 추출
            extract_dir = zip_path.parent / zip_path.stem
        
        # 이미 추출된 경우 스킵
        if extract_dir.exists():
            print(f"📂 이미 추출됨: {zip_path.name}")
            return extract_dir
        
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            print(f"📦 추출 완료: {zip_path.name} → {extract_dir}")
            return extract_dir
            
        except Exception as e:
            print(f"❌ 추출 실패: {zip_path.name} - {e}")
            return None
    
    def extract_all_zips(self, source_dir: Path) -> List[Path]:
        """디렉토리 내 모든 ZIP 파일 추출"""
        zip_files = list(source_dir.rglob("*.zip"))
        extracted_dirs = []
        
        print(f"🔍 ZIP 파일 {len(zip_files)}개 발견")
        
        for zip_file in zip_files:
            extracted_dir = self.extract_zip_file(zip_file)
            if extracted_dir:
                extracted_dirs.append(extracted_dir)
        
        return extracted_dirs
    
    def find_json_files(self, extracted_dirs: List[Path]) -> List[Path]:
        """추출된 디렉토리에서 JSON 파일 찾기"""
        json_files = []
        
        for extracted_dir in extracted_dirs:
            # visualinfo 폴더에서 JSON 파일 찾기
            visualinfo_dir = extracted_dir / "visualinfo"
            if visualinfo_dir.exists():
                json_files.extend(list(visualinfo_dir.glob("*.json")))
            
            # 다른 위치의 JSON 파일도 찾기
            json_files.extend(list(extracted_dir.rglob("*.json")))
        
        # 중복 제거
        json_files = list(set(json_files))
        print(f"📄 JSON 파일 {len(json_files)}개 발견")
        
        return json_files
    
    def process_directory(self, source_dir: Path) -> List[Path]:
        """디렉토리 전체 처리"""
        print(f"🚀 처리 시작: {source_dir}")
        
        # ZIP 파일 추출
        extracted_dirs = self.extract_all_zips(source_dir)
        
        # JSON 파일 찾기
        json_files = self.find_json_files(extracted_dirs)
        
        return json_files


def main():
    """테스트용 메인 함수"""
    source_dir = Path(r"C:\Users\User\Downloads\250812_전체_박선화\1페이지-그림+비교표+테이블 삽입")
    
    if not source_dir.exists():
        print(f"❌ 소스 디렉토리를 찾을 수 없습니다: {source_dir}")
        return
    
    processor = ZipProcessor()
    json_files = processor.process_directory(source_dir)
    
    print(f"\n✅ 처리 완료: {len(json_files)}개 JSON 파일")
    for json_file in json_files[:5]:  # 처음 5개만 출력
        print(f"  📄 {json_file}")


if __name__ == "__main__":
    main()
