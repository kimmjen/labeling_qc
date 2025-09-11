#!/usr/bin/env python3
"""
PDF 업로더 - API를 통한 PDF 업로드 및 OCR 처리
"""

import requests
import json
import time
import zipfile
from pathlib import Path
from typing import Dict, Optional, Any
from tqdm import tqdm


class PDFUploader:
    """PDF 업로드 및 OCR 처리를 위한 API 클라이언트"""
    
    def __init__(self, base_url: str = "http://172.19.0.35/studio-lite/api/v1/dl"):
        # http://172.19.2.164
        # http://172.19.3.222
        # http://172.19.0.35
        self.base_url = base_url
        self.session = requests.Session()
        
    def upload_pdf(self, pdf_path: Path) -> Optional[Dict[str, Any]]:
        """
        PDF 파일을 업로드합니다.
        
        Args:
            pdf_path: PDF 파일 경로
            
        Returns:
            업로드 결과 정보 (fileId, fileName, numOfPages 등)
        """
        try:
            url = f"{self.base_url}/files/upload"
            
            with open(pdf_path, 'rb') as f:
                files = {'file': (pdf_path.name, f, 'application/pdf')}
                
                response = self.session.post(url, files=files)
                response.raise_for_status()
                
                result = response.json()
                
                if result.get('codeNum') == 0:
                    return result.get('data')
                else:
                    print(f"❌ 업로드 오류: {result.get('code', 'Unknown error')}")
                    return None
                    
        except requests.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 업로드 오류: {e}")
            return None
    
    def extract_pages(self, file_id: str, page_range: str) -> Optional[Dict[str, Any]]:
        """
        페이지 범위를 OCR 처리 요청합니다.
        
        Args:
            file_id: 업로드된 파일의 ID
            page_range: 페이지 범위 (예: "1-120")
            
        Returns:
            OCR 처리 결과 정보
        """
        try:
            url = f"{self.base_url}/files/{file_id}/extract-page"
            params = {'range': page_range}
            
            response = self.session.post(url, params=params)
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('codeNum') == 0:
                return result.get('data')
            else:
                print(f"❌ OCR 처리 오류: {result.get('code', 'Unknown error')}")
                return None
                
        except requests.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ OCR 처리 오류: {e}")
            return None
    
    def get_visual_info(self, file_id: str, engine: str = "pdf_ai_dl", ocr_mode: str = "AUTO", progress_callback=None) -> Optional[Dict[str, Any]]:
        """
        VisualInfo 결과를 조회합니다.
        
        Args:
            file_id: 업로드된 파일의 ID
            engine: OCR 엔진 (기본값: pdf_ai_dl)
            ocr_mode: OCR 모드 (기본값: AUTO)
            
        Returns:
            VisualInfo JSON 데이터
        """
        try:
            url = f"{self.base_url}/files/{file_id}/visualinfo"
            params = {
                'engine': engine,
                'ocrMode': ocr_mode
            }
            
            # OCR 처리가 완료될 때까지 대기 (최대 5분)
            max_retries = 30
            retry_count = 0
            
            while retry_count < max_retries:
                response = self.session.get(url, params=params)
                response.raise_for_status()
                
                # 응답이 JSON인지 확인
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    try:
                        result = response.json()
                        return result
                    except json.JSONDecodeError:
                        pass
                
                # OCR 처리 중이면 10초 대기 후 재시도
                if progress_callback:
                    progress_callback(f"OCR 대기 중... ({retry_count + 1}/{max_retries})")
                else:
                    print(f"⏳ OCR 처리 중... ({retry_count + 1}/{max_retries})")
                time.sleep(10)
                retry_count += 1
            
            print(f"❌ OCR 처리 시간 초과 ({max_retries * 10}초)")
            return None
                
        except requests.RequestException as e:
            print(f"❌ 네트워크 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ VisualInfo 조회 오류: {e}")
            return None
    
    def create_visualcontent_zip(self, pdf_path: Path, visual_info: Dict[str, Any], zip_path: Path, file_id: str = None) -> bool:
        """
        VisualContent ZIP 파일을 생성합니다.
        
        Args:
            pdf_path: 원본 PDF 파일 경로
            visual_info: VisualInfo JSON 데이터
            zip_path: 생성할 ZIP 파일 경로
            file_id: API에서 받은 fileId (가장 정확함)
            
        Returns:
            성공 여부
        """
        try:
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # 1. original 폴더에 PDF 파일 추가
                zipf.write(pdf_path, f"original/{pdf_path.name}")

                # 2. visualinfo 폴더에 JSON 파일 추가
                metadata = visual_info.get("metadata", {})
                
                # fileId 우선순위: 매개변수 > visual_info.metadata.fileId
                actual_file_id = file_id or metadata.get("fileId")
                if not actual_file_id:
                    raise ValueError("fileId를 찾을 수 없습니다.")

                json_filename = f"{actual_file_id}_visualinfo.json"
                json_content = json.dumps(visual_info, ensure_ascii=False, indent=2)
                zipf.writestr(f"visualinfo/{json_filename}", json_content.encode('utf-8'))
                
                # 3. meta 폴더에 메타데이터 추가
                meta_data = {
                    "fileId": actual_file_id,
                    "fileName": metadata.get("fileName", pdf_path.name),
                    "created": metadata.get("created", ""),
                    "processing": {
                        "engine": metadata.get("engine", "pdf_ai_dl"),
                        "ocrMode": metadata.get("ocrMode", "AUTO")
                    }
                }
                meta_filename = f"{actual_file_id}_meta.json"
                meta_content = json.dumps(meta_data, ensure_ascii=False, indent=2)
                zipf.writestr(f"meta/{meta_filename}", meta_content.encode('utf-8'))
            
            return True
            
        except Exception as e:
            print(f"❌ ZIP 파일 생성 오류: {e}")
            return False
