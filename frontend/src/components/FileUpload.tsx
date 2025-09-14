import React, { useState, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Upload,
  File,
  CheckCircle,
  AlertTriangle,
  X,
  Download,
  Brain,
  Zap
} from 'lucide-react';
import axios from 'axios';
import type { ValidationResult, QualityIssue, AIAnalysis } from '../types/api';

const FileUpload: React.FC = () => {
  const [isDragging, setIsDragging] = useState(false);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files).filter(
      file => file.name.endsWith('.json')
    );

    if (files.length > 0) {
      setUploadedFiles(prev => [...prev, ...files]);
    }
  }, []);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []).filter(
      file => file.name.endsWith('.json')
    );

    if (files.length > 0) {
      setUploadedFiles(prev => [...prev, ...files]);
    }
  }, []);

  const removeFile = useCallback((index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
    setValidationResults(prev => prev.filter((_, i) => i !== index));
  }, []);

  const processFiles = useCallback(async () => {
    if (uploadedFiles.length === 0) return;

    setIsProcessing(true);
    const results: ValidationResult[] = [];

    try {
      for (const file of uploadedFiles) {
        const formData = new FormData();
        formData.append('file', file);

        // Flask 백엔드 API 호출
        const response = await axios.post<ValidationResult>(
          'http://localhost:5000/upload',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data',
            },
          }
        );

        results.push(response.data);
      }

      setValidationResults(results);
    } catch (error) {
      console.error('파일 처리 중 오류:', error);
      // 데모용 더미 데이터
      const dummyResults: ValidationResult[] = uploadedFiles.map((file, index) => ({
        filename: file.name,
        issues_count: Math.floor(Math.random() * 10) + 1,
        issues: [
          {
            rule_id: 'R004',
            severity: 'warning' as const,
            message: '날짜 형식이 일치하지 않습니다',
            file_path: file.name,
            element_id: 'elem_123',
            page_index: 0,
            category: 'label_type',
            suggested_fix: 'Date 라벨로 변경',
            auto_fixable: true
          }
        ],
        ai_analysis: {
          anomalies: [
            {
              type: '라벨 편중',
              message: 'ParaText 라벨이 과도하게 사용됨',
              severity: 'warning' as const
            }
          ],
          optimizations: {
            immediate_actions: ['빈 텍스트 요소 제거'],
            process_improvements: ['날짜 형식 가이드라인 수립'],
            automation_opportunities: ['자동 라벨링 시스템 도입']
          },
          quality_score: Math.floor(Math.random() * 20) + 80
        }
      }));
      setValidationResults(dummyResults);
    } finally {
      setIsProcessing(false);
    }
  }, [uploadedFiles]);

  const getQualityColor = (score: number) => {
    if (score >= 90) return 'text-success-600 bg-success-100';
    if (score >= 70) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'error': return 'text-error-600 bg-error-100';
      case 'warning': return 'text-warning-600 bg-warning-100';
      default: return 'text-primary-600 bg-primary-100';
    }
  };

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">파일 검수</h1>
        <p className="text-gray-600 mt-1">JSON 라벨링 파일을 업로드하여 AI 기반 품질 검수를 실행하세요</p>
      </div>

      {/* 파일 업로드 영역 */}
      <div className="card">
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={`
            border-2 border-dashed rounded-xl p-12 text-center transition-all duration-300
            ${isDragging 
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
            }
          `}
        >
          <Upload className="w-12 h-12 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            파일을 드래그하거나 클릭하여 업로드
          </h3>
          <p className="text-gray-600 mb-4">JSON 파일만 지원됩니다</p>

          <input
            type="file"
            multiple
            accept=".json"
            onChange={handleFileSelect}
            className="hidden"
            id="file-upload"
          />
          <label
            htmlFor="file-upload"
            className="btn-primary cursor-pointer inline-flex items-center"
          >
            <File className="w-4 h-4 mr-2" />
            파일 선택
          </label>
        </div>
      </div>

      {/* 업로드된 파일 목록 */}
      <AnimatePresence>
        {uploadedFiles.length > 0 && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="card"
          >
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">
                업로드된 파일 ({uploadedFiles.length}개)
              </h3>
              <motion.button
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                onClick={processFiles}
                disabled={isProcessing}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {isProcessing ? (
                  <>
                    <motion.div
                      animate={{ rotate: 360 }}
                      transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                      className="w-4 h-4 mr-2"
                    >
                      <Zap className="w-4 h-4" />
                    </motion.div>
                    처리 중...
                  </>
                ) : (
                  <>
                    <Brain className="w-4 h-4 mr-2" />
                    AI 검수 시작
                  </>
                )}
              </motion.button>
            </div>

            <div className="space-y-3">
              {uploadedFiles.map((file, index) => (
                <motion.div
                  key={`${file.name}-${index}`}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div className="flex items-center space-x-3">
                    <File className="w-5 h-5 text-blue-600" />
                    <div>
                      <p className="font-medium text-gray-900">{file.name}</p>
                      <p className="text-sm text-gray-500">{(file.size / 1024).toFixed(1)} KB</p>
                    </div>
                  </div>

                  <button
                    onClick={() => removeFile(index)}
                    className="p-2 hover:bg-gray-200 rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-gray-500" />
                  </button>
                </motion.div>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* 검수 결과 */}
      <AnimatePresence>
        {validationResults.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            className="space-y-6"
          >
            <h3 className="text-2xl font-bold text-gray-900">검수 결과</h3>

            {validationResults.map((result, index) => (
              <motion.div
                key={index}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.1 }}
                className="card"
              >
                {/* 파일 헤더 */}
                <div className="flex items-center justify-between mb-6 pb-4 border-b border-gray-200">
                  <div>
                    <h4 className="text-lg font-semibold text-gray-900">{result.filename}</h4>
                    <div className="flex items-center space-x-4 mt-2">
                      <span className="text-sm text-gray-600">
                        발견된 이슈: <span className="font-medium">{result.issues_count}개</span>
                      </span>
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getQualityColor(result.ai_analysis.quality_score)}`}>
                        품질점수: {result.ai_analysis.quality_score}점
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <motion.button
                      whileHover={{ scale: 1.05 }}
                      className="btn-secondary text-sm"
                    >
                      <Download className="w-4 h-4 mr-2" />
                      보고서 다운로드
                    </motion.button>
                  </div>
                </div>

                {/* 이슈 목록 */}
                {result.issues.length > 0 && (
                  <div className="mb-6">
                    <h5 className="font-semibold text-gray-900 mb-3">발견된 이슈</h5>
                    <div className="space-y-2">
                      {result.issues.map((issue, issueIndex) => (
                        <div key={issueIndex} className="flex items-start space-x-3 p-3 bg-gray-50 rounded-lg">
                          <div className={`w-2 h-2 rounded-full mt-2 ${getSeverityColor(issue.severity).split(' ')[1]}`} />
                          <div className="flex-1">
                            <div className="flex items-center space-x-2 mb-1">
                              <span className={`px-2 py-1 rounded text-xs font-medium ${getSeverityColor(issue.severity)}`}>
                                {issue.rule_id}
                              </span>
                              <span className="text-sm font-medium text-gray-900">{issue.message}</span>
                            </div>
                            {issue.suggested_fix && (
                              <p className="text-sm text-gray-600">💡 {issue.suggested_fix}</p>
                            )}
                          </div>
                          {issue.auto_fixable && (
                            <CheckCircle className="w-4 h-4 text-success-500 mt-1" />
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* AI 분석 결과 */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* 이상 패턴 */}
                  <div>
                    <h6 className="font-medium text-gray-900 mb-2">🔍 이상 패턴</h6>
                    <div className="space-y-2">
                      {result.ai_analysis.anomalies.map((anomaly, aIndex) => (
                        <div key={aIndex} className="text-sm">
                          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${getSeverityColor(anomaly.severity).split(' ')[1]}`} />
                          {anomaly.message}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 즉시 조치 */}
                  <div>
                    <h6 className="font-medium text-gray-900 mb-2">⚡ 즉시 조치</h6>
                    <div className="space-y-1">
                      {result.ai_analysis.optimizations.immediate_actions.map((action, aIndex) => (
                        <div key={aIndex} className="text-sm text-gray-600">
                          • {action}
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* 자동화 기회 */}
                  <div>
                    <h6 className="font-medium text-gray-900 mb-2">🤖 자동화 기회</h6>
                    <div className="space-y-1">
                      {result.ai_analysis.optimizations.automation_opportunities.map((opportunity, oIndex) => (
                        <div key={oIndex} className="text-sm text-gray-600">
                          • {opportunity}
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </motion.div>
            ))}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FileUpload;
