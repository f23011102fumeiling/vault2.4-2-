from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

from app.database import get_db
from app.models.user import User
from app.models.survey import Survey as SurveyModel, Question as QuestionModel, SurveyResponse as SurveyResponseModel
from app.utils.auth import get_current_user

router = APIRouter()

# Pydantic响应模型定义
class QuestionResponse(BaseModel):
    id: str
    text: str
    type: str
    options: List[str] | None = None
    required: bool = True

class SurveyResponse(BaseModel):
    id: str
    title: str
    description: str | None = None
    status: str
    questions: List[QuestionResponse]

class SurveySubmission(BaseModel):
    answers: Dict[str, Any]


def _get_student_class_ids(db: Session, student_id: str) -> List[str]:
    """获取学生已加入的班级ID列表"""
    try:
        rows = db.execute(
            text("""
                SELECT class_id FROM class_students
                WHERE student_id = :student_id AND status = 'active'
            """),
            {"student_id": str(student_id)}
        ).fetchall()
        return [str(r.class_id) for r in rows] if rows else []
    except Exception as e:
        print(f"学生班级查询失败 student_id={student_id}: {e}")
        return []


@router.get("")
async def get_surveys(
    release_type: Optional[str] = Query(None, description="发布类型: in_class=课堂检测, homework=课后作业, practice=自主练习"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取学生可用的已发布问卷列表。
    仅返回：1) 已发布 2) 发布到当前学生所在班级 3) 可选按发布类型筛选。
    """
    try:
        if getattr(current_user, "role", None) != "student":
            raise HTTPException(status_code=403, detail="只有学生可以访问此接口")
        student_id = str(current_user.id)
        class_ids = _get_student_class_ids(db, student_id)
        if not class_ids:
            return []
        # 兼容：若表尚无 release_type/target_class_ids 列（未执行迁移），避免 500，返回空列表
        surveys = []
        try:
            query = db.query(SurveyModel).filter(SurveyModel.status == "published")
            if release_type:
                query = query.filter(SurveyModel.release_type == release_type)
            surveys = query.order_by(SurveyModel.published_at.desc()).all()
        except (ProgrammingError, Exception) as e:
            # 打印完整异常信息用于调试
            print(f"学生问卷列表查询异常: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            err_msg = str(e).lower()
            if "release_type" in err_msg or "target_class_ids" in err_msg or "column" in err_msg:
                print("学生问卷列表: 检测到表结构未迁移(release_type/target_class_ids)，请执行 backend/database/migrate_survey_release.sql")
                return []
            raise
        result = []
        for survey in surveys:
            target_ids = getattr(survey, "target_class_ids", None) or []
            legacy_class_id = getattr(survey, "class_id", None)
            visible = False
            if target_ids:
                visible = any(str(cid) in class_ids for cid in (target_ids if isinstance(target_ids, list) else []))
            elif legacy_class_id:
                visible = str(legacy_class_id) in class_ids
            if not visible:
                continue
            question_count = db.query(QuestionModel).filter(QuestionModel.survey_id == survey.id).count()
            end_time = getattr(survey, "end_time", None)
            result.append({
                "id": str(survey.id),
                "title": survey.title,
                "description": survey.description or "",
                "questionCount": question_count,
                "status": "published",
                "releaseType": getattr(survey, "release_type", None) or "in_class",
                "publishedAt": survey.published_at.strftime("%Y-%m-%d") if survey.published_at else None,
                "dueDate": end_time.strftime("%Y-%m-%d") if end_time else None,
            })
        return result
    except HTTPException:
        raise
    except Exception as e:
        print(f"学生问卷列表异常: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"获取问卷列表失败: {str(e)}")


@router.get("/{survey_id}", response_model=SurveyResponse)
async def get_survey_detail(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取问卷详情（仅已发布且对当前学生可见的问卷）
    """
    if getattr(current_user, "role", None) != "student":
        raise HTTPException(status_code=403, detail="只有学生可以访问此接口")
    survey = db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
    if not survey or survey.status != "published":
        raise HTTPException(status_code=404, detail="问卷不存在或未发布")
    class_ids = _get_student_class_ids(db, str(current_user.id))
    target_ids = getattr(survey, "target_class_ids", None) or []
    legacy_class_id = getattr(survey, "class_id", None)
    visible = (target_ids and any(cid in class_ids for cid in (target_ids if isinstance(target_ids, list) else []))) or (
        legacy_class_id and str(legacy_class_id) in class_ids
    )
    if not visible:
        raise HTTPException(status_code=404, detail="问卷不存在或未发布")
    questions = db.query(QuestionModel).filter(QuestionModel.survey_id == survey_id).order_by(QuestionModel.question_order).all()
    
    def normalize_options(options):
        if not options:
            return None
        if isinstance(options, list):
            normalized = []
            for opt in options:
                if isinstance(opt, dict):
                    key = opt.get('key', '')
                    value = opt.get('value', '')
                    normalized.append(f"{key}. {value}" if key else str(value))
                else:
                    normalized.append(str(opt))
            return normalized
        return options
    
    return SurveyResponse(
        id=str(survey.id),
        title=survey.title,
        description=survey.description or "",
        status=survey.status,
        questions=[
            QuestionResponse(
                id=str(q.id),
                text=q.question_text,
                type=q.question_type,
                options=normalize_options(q.options),
                required=q.is_required,
            )
            for q in questions
        ]
    )


@router.get("/{survey_id}/my-result")
async def get_my_result(
    survey_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    获取当前学生在该问卷下的作答状态与成绩。
    用于「查看详情」：已提交且 total_score 不为空视为老师已公布成绩，可显示分数；否则显示「等待老师公布成绩」。
    """
    if getattr(current_user, "role", None) != "student":
        raise HTTPException(status_code=403, detail="只有学生可以访问此接口")
    from uuid import UUID
    from app.models.survey import Answer as AnswerModel
    try:
        sid = current_user.id if hasattr(current_user.id, 'hex') else UUID(str(current_user.id))
    except Exception:
        sid = UUID(str(current_user.id))
    response = (
        db.query(SurveyResponseModel)
        .filter(
            SurveyResponseModel.survey_id == survey_id,
            SurveyResponseModel.student_id == sid,
        )
        .order_by(SurveyResponseModel.attempt_number.desc())
        .first()
    )
    if not response:
        return {"submitted": False}
    submitted = response.submit_time is not None
    score_published = response.total_score is not None
    
    # 获取详细答案和AI打分结果
    answers = db.query(AnswerModel).filter(
        AnswerModel.response_id == response.id
    ).all()
    
    detailed_answers = []
    for ans in answers:
        answer_data = {
            "questionId": str(ans.question_id),
            "studentAnswer": ans.student_answer,
            "isCorrect": ans.is_correct,
            "score": float(ans.score) if ans.score is not None else None,
        }
        
        # 如果有AI打分结果，解析teacher_comment
        if ans.teacher_comment:
            try:
                import json
                grading_result = json.loads(ans.teacher_comment)
                answer_data["gradingResult"] = grading_result
            except:
                pass
        
        detailed_answers.append(answer_data)
    
    return {
        "submitted": submitted,
        "scorePublished": score_published,
        "totalScore": float(response.total_score) if response.total_score is not None else None,
        "percentageScore": float(response.percentage_score) if response.percentage_score is not None else None,
        "submitTime": response.submit_time.isoformat() if response.submit_time else None,
        "isPassed": response.is_passed,
        "answers": detailed_answers
    }


@router.post("/{survey_id}/submit")
async def submit_survey(
    survey_id: str,
    submission: SurveySubmission,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    提交问卷答案。会写入 survey_responses 与 answers；若已有提交记录则更新或按 attempt 追加。
    """
    print(f"=" * 70)
    print(f"📝 学生提交问卷 - 开始")
    print(f"问卷ID: {survey_id}")
    print(f"学生ID: {current_user.id}")
    print(f"学生角色: {getattr(current_user, 'role', None)}")
    print(f"提交答案数量: {len(submission.answers) if submission.answers else 0}")
    print(f"=" * 70)
    
    if getattr(current_user, "role", None) != "student":
        print(f"❌ 权限验证失败：用户角色不是学生")
        raise HTTPException(status_code=403, detail="只有学生可以访问此接口")
    
    print(f"✅ 权限验证通过")
    
    survey = db.query(SurveyModel).filter(SurveyModel.id == survey_id).first()
    if not survey or survey.status != "published":
        print(f"❌ 问卷验证失败：问卷不存在或未发布")
        raise HTTPException(status_code=404, detail="问卷不存在或未发布")
    
    print(f"✅ 问卷验证通过: {survey.title}")
    
    class_ids = _get_student_class_ids(db, str(current_user.id))
    print(f"📚 学生所在班级: {class_ids}")
    
    target_ids = getattr(survey, "target_class_ids", None) or []
    legacy_class_id = getattr(survey, "class_id", None)
    visible = (target_ids and any(str(cid) in class_ids for cid in (target_ids if isinstance(target_ids, list) else []))) or (
        legacy_class_id and str(legacy_class_id) in class_ids
    )
    if not visible:
        print(f"❌ 班级权限验证失败：学生不在目标班级中")
        raise HTTPException(status_code=404, detail="问卷不存在或未发布")
    
    print(f"✅ 班级权限验证通过")
    
    from datetime import datetime
    from uuid import UUID
    try:
        sid = current_user.id if hasattr(current_user.id, 'hex') else UUID(str(current_user.id))
    except Exception:
        sid = UUID(str(current_user.id))
    
    existing = (
        db.query(SurveyResponseModel)
        .filter(
            SurveyResponseModel.survey_id == survey_id,
            SurveyResponseModel.student_id == sid,
        )
        .order_by(SurveyResponseModel.attempt_number.desc())
        .first()
    )
    
    print(f"📊 已有提交记录: {'是' if existing else '否'}")
    
    if not survey.allow_multiple_attempts:
        if existing:
            print(f"❌ 多次提交检查失败：不允许多次作答")
            raise HTTPException(
                status_code=400,
                detail="该问卷不允许多次作答，您已经提交过了"
            )
    else:
        existing_attempts = db.query(SurveyResponseModel).filter(
            SurveyResponseModel.survey_id == survey_id,
            SurveyResponseModel.student_id == sid,
        ).count()
        if existing_attempts >= survey.max_attempts:
            print(f"❌ 多次提交检查失败：已达到最大作答次数")
            raise HTTPException(
                status_code=400,
                detail=f"您已达到最大作答次数（{survey.max_attempts}次）"
            )
    
    print(f"✅ 多次提交检查通过")
    
    attempt = (existing.attempt_number + 1) if existing else 1
    resp = SurveyResponseModel(
        survey_id=UUID(survey_id),
        student_id=sid,
        attempt_number=attempt,
        status="completed",
        submit_time=datetime.utcnow(),
    )
    db.add(resp)
    db.flush()
    
    print(f"✅ 创建提交记录: response_id={resp.id}, attempt_number={attempt}")
    
    answers = submission.answers or {}
    total_score = 0
    answer_count = 0
    
    from app.services.essay_grading_service import essay_grading_service
    
    for qid, ans in answers.items():
        from app.models.survey import Answer as AnswerModel
        
        question = db.query(QuestionModel).filter(
            QuestionModel.id == UUID(qid)
        ).first()
        
        if not question:
            print(f"⚠️ 题目不存在: question_id={qid}")
            continue
        
        is_correct = False
        score = 0
        teacher_comment = None
        
        if question.question_type in ['single_choice', 'judgment']:
            correct_answer = question.correct_answer
            if correct_answer:
                if isinstance(correct_answer, list):
                    is_correct = ans in correct_answer
                else:
                    student_answer = str(ans).strip()
                    correct_answer_str = str(correct_answer).strip()
                    if '.' in student_answer:
                        student_answer = student_answer.split('.')[0].strip()
                    is_correct = student_answer == correct_answer_str
                if is_correct:
                    score = float(question.score)
        elif question.question_type == 'multiple_choice':
            correct_answer = question.correct_answer
            if correct_answer and isinstance(ans, list):
                if isinstance(correct_answer, list):
                    student_answers = []
                    for a in ans:
                        a_str = str(a).strip()
                        if '.' in a_str:
                            a_str = a_str.split('.')[0].strip()
                        student_answers.append(a_str)
                    is_correct = set(student_answers) == set(correct_answer)
                else:
                    is_correct = ans == correct_answer
                if is_correct:
                    score = float(question.score)
        elif question.question_type in ['text', 'fill_blank']:
            correct_answer = question.correct_answer
            if correct_answer:
                student_answer = str(ans).strip() if ans else ""
                
                if isinstance(correct_answer, list):
                    is_correct = student_answer in [str(item).strip() for item in correct_answer]
                else:
                    correct_answer_str = str(correct_answer).strip()
                    is_correct = student_answer == correct_answer_str
                
                if is_correct:
                    score = float(question.score)
        elif question.question_type == 'essay' and survey.survey_type == 'exam':
            print(f"📝 问答题AI打分: question_type={question.question_type}, survey_type={survey.survey_type}")
            
            try:
                grading_result = await essay_grading_service.grade_essay(
                    question_text=question.question_text,
                    question_type=question.question_type,
                    reference_answer=question.correct_answer,
                    grading_criteria=question.grading_criteria,
                    min_word_count=question.min_word_count,
                    student_answer=str(ans) if ans else "",
                    max_score=float(question.score)
                )
                
                score = grading_result.get('score', 0)
                is_correct = grading_result.get('percentage', 0) >= 60
                teacher_comment = json.dumps(grading_result, ensure_ascii=False)
                
                print(f"✅ AI打分完成: score={score}, is_correct={is_correct}")
                
            except Exception as e:
                print(f"❌ AI打分失败: {e}")
                import traceback
                traceback.print_exc()
                score = 0
                is_correct = False
                teacher_comment = f"AI打分失败: {str(e)}"
        elif question.question_type == 'essay' and survey.survey_type == 'questionnaire':
            correct_answer = question.correct_answer
            if correct_answer:
                student_answer = str(ans).strip() if ans else ""
                
                if isinstance(correct_answer, list):
                    is_correct = student_answer in [str(item).strip() for item in correct_answer]
                else:
                    correct_answer_str = str(correct_answer).strip()
                    is_correct = student_answer == correct_answer_str
                
                if is_correct:
                    score = float(question.score)
        
        total_score += score
        answer_count += 1
        
        a = AnswerModel(
            response_id=resp.id,
            question_id=UUID(qid),
            student_answer=ans,
            is_correct=is_correct,
            score=score,
            teacher_comment=teacher_comment,
            auto_graded=True,
        )
        db.add(a)
    
    print(f"✅ 保存答案记录: {answer_count} 个答案, 总分: {total_score}")
    
    resp.total_score = total_score
    resp.percentage_score = (total_score / survey.total_score * 100) if survey.total_score > 0 else 0
    resp.is_passed = resp.percentage_score >= survey.pass_score if survey.pass_score else None
    
    print(f"📊 计算得分: total_score={total_score}, percentage_score={resp.percentage_score}, is_passed={resp.is_passed}")
    
    db.commit()
    
    print(f"✅ 数据库提交成功")
    print(f"=" * 70)
    print(f"🎉 问卷提交完成")
    print(f"=" * 70)
    
    return {
        "message": "问卷提交成功",
        "survey_id": survey_id,
        "total_score": total_score,
        "percentage_score": resp.percentage_score,
        "is_passed": resp.is_passed
    }
