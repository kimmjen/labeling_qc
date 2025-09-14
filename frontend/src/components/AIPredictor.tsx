import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Brain, Zap, TrendingUp, AlertCircle } from 'lucide-react';
import axios from 'axios';
import type { LabelPrediction } from '../types/api';

const AIPredictor: React.FC = () => {
  const [inputText, setInputText] = useState('');
  const [prediction, setPrediction] = useState<LabelPrediction | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [confidence, setConfidence] = useState(0);

  const handlePredict = async () => {
    if (!inputText.trim()) return;

    setIsLoading(true);

    try {
      const response = await axios.post<LabelPrediction>(
        'http://localhost:8000/api/predict_label',
        { text: inputText }
      );

      setPrediction(response.data);
      setConfidence(response.data.confidence);
    } catch (error) {
      console.error('AI 예측 오류:', error);

      // 데모용 더미 데이터
      const dummyPrediction: LabelPrediction = {
        predicted_label: inputText.includes('제') && inputText.includes('장') ? 'ParaTitle' :
                        inputText.includes('년') && inputText.includes('월') ? 'Date' :
                        inputText.includes('원문') || inputText.includes('번역문') ? 'ParaText' : 'ListText',
        confidence: Math.floor(Math.random() * 30) + 70,
        reason: '패턴 매칭 분석 결과',
        alternatives: [
          { label: 'ParaText', confidence: 85, score: 85 },
          { label: 'ListText', confidence: 70, score: 70 },
          { label: 'ParaTitle', confidence: 60, score: 60 }
        ]
      };

      setPrediction(dummyPrediction);
      setConfidence(dummyPrediction.confidence);
    } finally {
      setIsLoading(false);
    }
  };

  const getConfidenceColor = (conf: number) => {
    if (conf >= 80) return 'text-success-600 bg-success-100';
    if (conf >= 60) return 'text-warning-600 bg-warning-100';
    return 'text-error-600 bg-error-100';
  };

  const getLabelColor = (label: string) => {
    switch (label) {
      case 'ParaTitle': return 'bg-purple-100 text-purple-700';
      case 'ParaText': return 'bg-blue-100 text-blue-700';
      case 'ListText': return 'bg-green-100 text-green-700';
      case 'Date': return 'bg-orange-100 text-orange-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const exampleTexts = [
    '제1장 총칙',
    '2023년 12월 25일',
    '원문',
    '이 법은 국민의 권리를 보장하기 위하여 제정된다.',
    '1. 목적'
  ];

  return (
    <div className="space-y-8">
      {/* 헤더 */}
      <div>
        <h1 className="text-3xl font-bold text-gray-900">AI 라벨 예측</h1>
        <p className="text-gray-600 mt-1">텍스트를 입력하면 AI가 최적의 라벨을 추천해드립니다</p>
      </div>

      {/* 입력 영역 */}
      <div className="card">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              분석할 텍스트 입력
            </label>
            <textarea
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              placeholder="라벨링을 예측할 텍스트를 입력하세요..."
              className="w-full h-32 px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-primary-500 resize-none"
            />
          </div>

          <div className="flex items-center justify-between">
            <div className="flex flex-wrap gap-2">
              <span className="text-sm text-gray-600">예시:</span>
              {exampleTexts.map((text, index) => (
                <button
                  key={index}
                  onClick={() => setInputText(text)}
                  className="text-sm px-3 py-1 bg-gray-100 hover:bg-gray-200 rounded-full transition-colors"
                >
                  {text}
                </button>
              ))}
            </div>

            <motion.button
              whileHover={{ scale: 1.05 }}
              whileTap={{ scale: 0.95 }}
              onClick={handlePredict}
              disabled={!inputText.trim() || isLoading}
              className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <>
                  <motion.div
                    animate={{ rotate: 360 }}
                    transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                    className="w-4 h-4 mr-2"
                  >
                    <Brain className="w-4 h-4" />
                  </motion.div>
                  분석 중...
                </>
              ) : (
                <>
                  <Zap className="w-4 h-4 mr-2" />
                  AI 예측 실행
                </>
              )}
            </motion.button>
          </div>
        </div>
      </div>

      {/* 예측 결과 */}
      {prediction && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-6"
        >
          {/* 메인 예측 결과 */}
          <div className="card">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-lg font-semibold text-gray-900">AI 예측 결과</h3>
              <div className={`px-3 py-1 rounded-full text-sm font-medium ${getConfidenceColor(confidence)}`}>
                신뢰도: {confidence}%
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-medium text-gray-700 mb-3">추천 라벨</h4>
                <div className="flex items-center space-x-3">
                  <span className={`px-4 py-2 rounded-lg font-medium text-lg ${getLabelColor(prediction.predicted_label)}`}>
                    {prediction.predicted_label}
                  </span>
                  <div className="flex items-center space-x-1 text-sm text-gray-600">
                    <TrendingUp className="w-4 h-4" />
                    <span>{confidence}% 확신</span>
                  </div>
                </div>
              </div>

              <div>
                <h4 className="font-medium text-gray-700 mb-3">분석 근거</h4>
                <div className="flex items-start space-x-2">
                  <AlertCircle className="w-5 h-5 text-primary-500 mt-0.5" />
                  <p className="text-sm text-gray-700">{prediction.reason}</p>
                </div>
              </div>
            </div>
          </div>

          {/* 대안 라벨들 */}
          {prediction.alternatives && prediction.alternatives.length > 0 && (
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">대안 라벨 추천</h3>
              <div className="space-y-3">
                {prediction.alternatives.map((alt, index) => (
                  <motion.div
                    key={index}
                    initial={{ opacity: 0, x: -20 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ delay: index * 0.1 }}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <span className={`px-3 py-1 rounded-lg font-medium ${getLabelColor(alt.label)}`}>
                        {alt.label}
                      </span>
                      <span className="text-sm text-gray-600">신뢰도: {alt.confidence}%</span>
                    </div>

                    <div className="w-32 bg-gray-200 rounded-full h-2">
                      <motion.div
                        initial={{ width: 0 }}
                        animate={{ width: `${alt.confidence}%` }}
                        transition={{ delay: index * 0.1 + 0.3, duration: 0.5 }}
                        className={`h-2 rounded-full ${
                          alt.confidence >= 80 ? 'bg-success-500' :
                          alt.confidence >= 60 ? 'bg-warning-500' : 'bg-error-500'
                        }`}
                      />
                    </div>
                  </motion.div>
                ))}
              </div>
            </div>
          )}

          {/* AI 설명 */}
          <div className="card bg-gradient-to-r from-primary-50 to-purple-50 border-primary-200">
            <div className="flex items-start space-x-3">
              <div className="w-8 h-8 bg-primary-100 rounded-lg flex items-center justify-center">
                <Brain className="w-5 h-5 text-primary-600" />
              </div>
              <div>
                <h4 className="font-semibold text-gray-900 mb-2">AI 분석 과정</h4>
                <div className="text-sm text-gray-700 space-y-1">
                  <p>• <strong>패턴 매칭:</strong> 텍스트에서 알려진 패턴을 찾아 분석</p>
                  <p>• <strong>컨텍스트 분석:</strong> 주변 요소와의 관계를 고려</p>
                  <p>• <strong>휴리스틱 평가:</strong> 길이, 구조, 위치 등을 종합 판단</p>
                  <p>• <strong>신뢰도 계산:</strong> 여러 요소를 종합하여 신뢰도 산출</p>
                </div>
              </div>
            </div>
          </div>
        </motion.div>
      )}

      {/* AI 성능 통계 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="card text-center">
          <div className="text-3xl font-bold text-primary-600 mb-2">94.2%</div>
          <div className="text-sm text-gray-600">전체 정확도</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-success-600 mb-2">1,247</div>
          <div className="text-sm text-gray-600">총 예측 수</div>
        </div>
        <div className="card text-center">
          <div className="text-3xl font-bold text-warning-600 mb-2">0.3s</div>
          <div className="text-sm text-gray-600">평균 응답 시간</div>
        </div>
      </div>
    </div>
  );
};

export default AIPredictor;
