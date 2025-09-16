#!/usr/bin/env python3
"""
ChangeToListText - ListText 통일 + R003 법령 구조 적용 도구
"""

import json
import re
import zipfile
import shutil
import sys
from pathlib import Path
from tqdm import tqdm
import argparse


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


class ChangeToListText:
    def __init__(self, input_path):
        self.input_path = Path(input_path)
        
    def process_visualinfo_json(self, json_data):
        """
        visualinfo.json 데이터를 처리하여 ListText로 통일 후 R003 규칙 적용
        """
        elements = json_data.get('elements', [])
        changes = 0
        
        # 1단계: PageNumber 제외하고 모든 것을 ListText로 변경
        for element in elements:
            category = element.get('category', {})
            current_label = category.get('label', '')
            
            if current_label not in ['ListText', 'PageNumber']:
                category['label'] = 'ListText'
                category['type'] = 'LIST'
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
                    category['type'] = 'HEADING'
                    changes += 1
                # 제~편, 제~장, 제~절, 제~조 패턴
                elif re.search(r'^제\s*\d+\s*(편|장|절|관|조)', text):
                    category['label'] = 'ParaTitle'
                    category['type'] = 'HEADING'
                    changes += 1
        
        return changes
    
    def process_single_zip(self, zip_path, output_dir):
        """
        단일 ZIP 파일 처리
        """
        temp_dir = output_dir.parent / "temp_processing"
        temp_dir.mkdir(exist_ok=True)
        
        try:
            # 1. ZIP 파일 추출
            extract_dir = temp_dir / zip_path.stem
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            
            # 2. visualinfo.json 파일 찾기
            visualinfo_files = list(extract_dir.rglob("*_visualinfo.json"))
            if not visualinfo_files:
                print(f"⚠️ {zip_path.name}: visualinfo.json 파일 없음")
                return 0
            
            json_file = visualinfo_files[0]
            
            # 3. JSON 파일 처리
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            changes = self.process_visualinfo_json(data)
            
            if changes > 0:
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                print(f"✅ {zip_path.name}: {changes}개 항목 변경")
            else:
                print(f"📝 {zip_path.name}: 변경 사항 없음")
            
            # 4. 결과물 ZIP 파일 생성
            output_zip = output_dir / zip_path.name
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as new_zip:
                for file_to_zip in extract_dir.rglob('*'):
                    if file_to_zip.is_file():
                        arcname = file_to_zip.relative_to(extract_dir)
                        new_zip.write(file_to_zip, arcname)
            
            print(f"💾 저장됨: {output_zip}")
            return changes
            
        except Exception as e:
            print(f"❌ {zip_path.name} 처리 중 오류: {e}")
            return 0
        finally:
            # 임시 폴더 정리
            safe_rmtree(temp_dir)
    
    def process_directory(self, target_dir, output_dir):
        """
        디렉토리 내의 모든 ZIP 파일 처리
        """
        zip_files = list(target_dir.rglob("*.zip"))
        if not zip_files:
            print("❌ 처리할 ZIP 파일을 찾을 수 없습니다.")
            return 0
        
        total_changes = 0
        temp_processing_dir = output_dir.parent / "temp_processing_ListText"
        
        # 이전 임시 폴더 정리
        safe_rmtree(temp_processing_dir)
        temp_processing_dir.mkdir(exist_ok=True)
        
        print(f"📂 총 {len(zip_files)}개의 ZIP 파일을 처리합니다.")
        
        with tqdm(total=len(zip_files), desc="🚀 전체 진행률", unit="개") as pbar:
            for zip_path in zip_files:
                pbar.set_postfix_str(zip_path.name)
                
                try:
                    # 임시 추출
                    extract_dir = temp_processing_dir / zip_path.stem
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                    
                    # visualinfo.json 파일 찾기
                    visualinfo_files = list(extract_dir.rglob("*_visualinfo.json"))
                    if not visualinfo_files:
                        pbar.write(f"  ⚠️ {zip_path.name}: visualinfo.json 파일 없음")
                        # 원본 ZIP 그대로 복사
                        relative_path = zip_path.relative_to(target_dir)
                        dest_path = output_dir / relative_path
                        dest_path.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(zip_path, dest_path)
                        continue
                    
                    json_file = visualinfo_files[0]
                    
                    # JSON 파일 처리
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.loadnfff
                        
                    
                    changes = self.process_visualinfo_json(data)
                    
                    if changes > 0:
                        with open(json_file, 'w', encoding='utf-8') as f:
                            json.dump(data, f, ensure_ascii=False, indent=2)
                        total_changes += changes
                        pbar.write(f"  ✅ {zip_path.name}: {changes}개 항목 변경")
                    else:
                        pbar.write(f"  📝 {zip_path.name}: 변경 사항 없음")
                    
                    # 결과물 재압축 및 저장
                    relative_path = zip_path.relative_to(target_dir)
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
        
        # 최종 정리
        safe_rmtree(temp_processing_dir)
        return total_changes
    
    def run(self):
        """
        메인 실행 함수
        """
        print("📝 ListText 통일 + R003 법령 구조 적용 도구")
        print(f"📂 입력: {self.input_path}")
        
        if self.input_path.is_file() and self.input_path.suffix.lower() == '.zip':
            # 단일 ZIP 파일 처리
            output_dir = self.input_path.parent / f"{self.input_path.stem}_ListText"
            print(f"📄 단일 ZIP 파일 처리 모드")
            print(f"📁 출력: {output_dir}")
            
            # 이전 결과 폴더 삭제
            safe_rmtree(output_dir)
            
            total_changes = self.process_single_zip(self.input_path, output_dir)
            
        elif self.input_path.is_dir():
            # 폴더 처리
            output_dir = self.input_path.parent / f"{self.input_path.name}_ListText"
            print(f"📁 폴더 처리 모드")
            print(f"📁 출력: {output_dir}")
            
            # 이전 결과 폴더 삭제
            safe_rmtree(output_dir)
            output_dir.mkdir(exist_ok=True)
            
            total_changes = self.process_directory(self.input_path, output_dir)
            
        else:
            print("❌ 입력이 ZIP 파일이나 폴더가 아닙니다.")
            return False
        
        print(f"\n🎉 처리 완료! 총 {total_changes}개 항목이 변경되었습니다.")
        print(f"📂 결과는 {output_dir}에 저장되었습니다.")
        return True


def main():
    parser = argparse.ArgumentParser(
        description="ListText 통일 + R003 법령 구조 적용 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 단일 ZIP 파일 처리
  python ChangeToListText.py file.zip
  
  # 폴더 내 모든 ZIP 파일 처리
  python ChangeToListText.py /path/to/folder
  
적용 규칙:
  1. PageNumber를 제외한 모든 라벨을 ListText로 변경
  2. R003 법령 구조 규칙 적용:
     - ~법 → ParaTitle
     - 제~편/장/절/관/조 → ParaTitle
        """
    )
    
    parser.add_argument(
        "input_path", 
        help="처리할 ZIP 파일 또는 폴더 경로"
    )
    
    args = parser.parse_args()
    
    # 경로 검증
    input_path = Path(args.input_path)
    if not input_path.exists():
        print(f"❌ 경로를 찾을 수 없습니다: {input_path}")
        sys.exit(1)
    
    # 처리 실행
    processor = ChangeToListText(input_path)
    success = processor.run()
    
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main() 