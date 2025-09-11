#!/usr/bin/env python3
"""
ZIP 재압축 도구 - 수정된 파일들을 다시 ZIP으로 압축
"""

import zipfile
import shutil
import sys
from pathlib import Path
from typing import List

# 프로젝트 루트를 sys.path에 추가
sys.path.insert(0, str(Path(__file__).parent.parent))


class ZipRecompressor:
    """ZIP 재압축기"""
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("fixed_files")
        self.output_dir.mkdir(exist_ok=True)
    
    def recompress_directory(self, extracted_dir: Path) -> Path:
        """추출된 디렉토리를 다시 ZIP으로 압축"""
        zip_name = f"{extracted_dir.name}.zip"
        zip_path = self.output_dir / zip_name
        
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in extracted_dir.rglob('*'):
                    if file_path.is_file():
                        # 상대 경로로 추가
                        arcname = file_path.relative_to(extracted_dir)
                        zipf.write(file_path, arcname)
            
            print(f"📦 재압축 완료: {zip_name}")
            return zip_path
            
        except Exception as e:
            print(f"❌ 재압축 실패: {extracted_dir.name} - {e}")
            return None
    
    def recompress_all(self, extracted_base_dir: Path) -> List[Path]:
        """모든 추출된 디렉토리 재압축"""
        extracted_dirs = [d for d in extracted_base_dir.iterdir() if d.is_dir()]
        recompressed_files = []
        
        print(f"🔄 재압축 시작: {len(extracted_dirs)}개 디렉토리")
        
        for extracted_dir in extracted_dirs:
            zip_path = self.recompress_directory(extracted_dir)
            if zip_path:
                recompressed_files.append(zip_path)
        
        print(f"✅ 재압축 완료: {len(recompressed_files)}개 파일")
        return recompressed_files


def main():
    """테스트용 메인 함수"""
    extracted_base_dir = Path("extracted_data")
    
    if not extracted_base_dir.exists():
        print(f"❌ 추출된 데이터 디렉토리를 찾을 수 없습니다: {extracted_base_dir}")
        return
    
    recompressor = ZipRecompressor()
    recompressed_files = recompressor.recompress_all(extracted_base_dir)
    
    print(f"\n📦 재압축된 파일 목록:")
    for zip_file in recompressed_files:
        print(f"  📄 {zip_file}")


if __name__ == "__main__":
    main()
