import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { studentSurveyApi } from '@/services'

interface MyResult {
  submitted: boolean
  scorePublished?: boolean
  totalScore?: number
  percentageScore?: number
  submitTime?: string
  isPassed?: boolean
  answers?: Array<{
    questionId: string
    studentAnswer: any
    isCorrect?: boolean
    score?: number
    gradingResult?: {
      score: number
      max_score: number
      percentage: number
      level: string
      score_breakdown: {
        content_completeness: number
        accuracy: number
        depth: number
        expression: number
      }
      strengths: string[]
      areas_for_improvement: string[]
      comment: string
      detailed_feedback: Array<{
        point: string
        score: number
        max_score: number
        feedback: string
      }>
    }
  }>
}

const StudentSurveyDetail = () => {
  const { surveyId } = useParams<{ surveyId: string }>()
  const navigate = useNavigate()
  const [result, setResult] = useState<MyResult | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!surveyId) return
    studentSurveyApi
      .getMyResult(surveyId)
      .then((data: any) => setResult(data))
      .catch((e: any) => setError(e.response?.data?.detail || e.message || '加载失败'))
      .finally(() => setLoading(false))
  }, [surveyId])

  if (loading) {
    return (
      <div className="p-8 flex justify-center items-center min-h-[200px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    )
  }
  if (error) {
    return (
      <div className="p-8">
        <p className="text-red-600">{error}</p>
        <button
          type="button"
          onClick={() => navigate('/student/survey')}
          className="mt-4 px-4 py-2 bg-gray-200 rounded-lg"
        >
          返回问卷列表
        </button>
      </div>
    )
  }

  const submitted = result?.submitted ?? false
  const scorePublished = result?.scorePublished ?? false

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="mb-6">
        <button
          type="button"
          onClick={() => navigate('/student/survey')}
          className="text-gray-600 hover:text-gray-800 text-sm"
        >
          ← 返回问卷列表
        </button>
      </div>
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 text-center">
        {!submitted ? (
          <>
            <div className="text-6xl mb-4">📝</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">您还未作答</h2>
            <p className="text-gray-500 mb-6">请先完成该问卷的作答后再查看详情。</p>
            <button
              type="button"
              onClick={() => navigate(`/student/survey/${surveyId}/take`)}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700"
            >
              开始答题
            </button>
          </>
        ) : !scorePublished ? (
          <>
            <div className="text-6xl mb-4">⏳</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-2">等待老师公布成绩</h2>
            <p className="text-gray-500">您已提交答卷，成绩公布后可在此查看得分与详情。</p>
          </>
        ) : (
          <>
            <div className="text-6xl mb-4">📊</div>
            <h2 className="text-xl font-semibold text-gray-800 mb-4">成绩详情</h2>
            <div className="space-y-2 text-left max-w-xs mx-auto">
              {result?.totalScore != null && (
                <p className="text-gray-700">
                  <span className="font-medium">得分：</span>
                  {result.totalScore} 分
                </p>
              )}
              {result?.percentageScore != null && (
                <p className="text-gray-700">
                  <span className="font-medium">得分率：</span>
                  {result.percentageScore}%
                </p>
              )}
              {result?.isPassed != null && (
                <p className="text-gray-700">
                  <span className="font-medium">结果：</span>
                  {result.isPassed ? '通过' : '未通过'}
                </p>
              )}
              {result?.submitTime && (
                <p className="text-gray-500 text-sm">
                  提交时间：{new Date(result.submitTime).toLocaleString()}
                </p>
              )}
            </div>
            
            {result?.answers && result.answers.length > 0 && (
              <div className="mt-8 text-left">
                <h3 className="text-lg font-semibold text-gray-800 mb-4">详细答题情况</h3>
                <div className="space-y-6">
                  {result.answers.map((answer, index) => (
                    <div key={answer.questionId} className="bg-gray-50 rounded-lg p-6">
                      <div className="flex items-start justify-between mb-3">
                        <h4 className="font-medium text-gray-800">题目 {index + 1}</h4>
                        {answer.score !== undefined && (
                          <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                            answer.isCorrect ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                          }`}>
                            {answer.score} 分
                          </span>
                        )}
                      </div>
                      
                      <div className="mb-3">
                        <p className="text-sm text-gray-600 mb-1">你的答案：</p>
                        <p className="text-gray-800 bg-white p-3 rounded border border-gray-200">
                          {typeof answer.studentAnswer === 'string' ? answer.studentAnswer : JSON.stringify(answer.studentAnswer)}
                        </p>
                      </div>
                      
                      {answer.gradingResult && (
                        <div className="space-y-4">
                          <div className="bg-blue-50 rounded-lg p-4">
                            <div className="flex items-center gap-2 mb-2">
                              <span className="text-2xl">📝</span>
                              <span className="font-semibold text-gray-800">AI 评分结果</span>
                            </div>
                            
                            <div className="grid grid-cols-2 gap-3 mb-3">
                              <div className="bg-white rounded p-3">
                                <p className="text-sm text-gray-600">得分</p>
                                <p className="text-2xl font-bold text-blue-600">
                                  {answer.gradingResult.score} / {answer.gradingResult.max_score}
                                </p>
                              </div>
                              <div className="bg-white rounded p-3">
                                <p className="text-sm text-gray-600">等级</p>
                                <p className={`text-2xl font-bold ${
                                  answer.gradingResult.level === '满分' ? 'text-green-600' :
                                  answer.gradingResult.level === '优秀' ? 'text-blue-600' :
                                  answer.gradingResult.level === '良好' ? 'text-yellow-600' :
                                  answer.gradingResult.level === '及格' ? 'text-orange-600' :
                                  'text-red-600'
                                }`}>
                                  {answer.gradingResult.level}
                                </p>
                              </div>
                            </div>
                            
                            <div className="bg-white rounded p-3 mb-3">
                              <p className="text-sm text-gray-600 mb-2">评分细则</p>
                              <div className="space-y-2">
                                <div className="flex justify-between">
                                  <span className="text-sm text-gray-700">内容完整性</span>
                                  <span className="text-sm font-medium">{answer.gradingResult.score_breakdown.content_completeness} 分</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-sm text-gray-700">准确性</span>
                                  <span className="text-sm font-medium">{answer.gradingResult.score_breakdown.accuracy} 分</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-sm text-gray-700">深度</span>
                                  <span className="text-sm font-medium">{answer.gradingResult.score_breakdown.depth} 分</span>
                                </div>
                                <div className="flex justify-between">
                                  <span className="text-sm text-gray-700">表达</span>
                                  <span className="text-sm font-medium">{answer.gradingResult.score_breakdown.expression} 分</span>
                                </div>
                              </div>
                            </div>
                            
                            {answer.gradingResult.strengths && answer.gradingResult.strengths.length > 0 && (
                              <div className="bg-green-50 rounded p-3 mb-3">
                                <p className="text-sm text-gray-700 mb-2">✨ 优点</p>
                                <ul className="space-y-1">
                                  {answer.gradingResult.strengths.map((strength, idx) => (
                                    <li key={idx} className="text-sm text-gray-700">• {strength}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            {answer.gradingResult.areas_for_improvement && answer.gradingResult.areas_for_improvement.length > 0 && (
                              <div className="bg-yellow-50 rounded p-3 mb-3">
                                <p className="text-sm text-gray-700 mb-2">💡 改进建议</p>
                                <ul className="space-y-1">
                                  {answer.gradingResult.areas_for_improvement.map((suggestion, idx) => (
                                    <li key={idx} className="text-sm text-gray-700">• {suggestion}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                            
                            <div className="bg-purple-50 rounded p-3">
                              <p className="text-sm text-gray-700 mb-2">💬 综合评语</p>
                              <p className="text-sm text-gray-800">{answer.gradingResult.comment}</p>
                            </div>
                            
                            {answer.gradingResult.detailed_feedback && answer.gradingResult.detailed_feedback.length > 0 && (
                              <div className="mt-4">
                                <p className="text-sm text-gray-700 mb-2">📋 详细反馈</p>
                                <div className="space-y-2">
                                  {answer.gradingResult.detailed_feedback.map((feedback, idx) => (
                                    <div key={idx} className="bg-white rounded p-3 border border-gray-200">
                                      <div className="flex justify-between items-center mb-1">
                                        <span className="text-sm font-medium text-gray-800">{feedback.point}</span>
                                        <span className="text-sm text-gray-600">
                                          {feedback.score} / {feedback.max_score}
                                        </span>
                                      </div>
                                      <p className="text-sm text-gray-700">{feedback.feedback}</p>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}

export default StudentSurveyDetail
