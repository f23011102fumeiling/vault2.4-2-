from app.database import SessionLocal
from app.models.survey import Question

db = SessionLocal()

# 查询所有选择题
choice_questions = db.query(Question).filter(
    Question.question_type.in_(['single_choice', 'choice', 'multiple_choice'])
).all()

print(f"找到 {len(choice_questions)} 道选择题:")
for q in choice_questions:
    print(f"\n题目ID: {q.id}")
    print(f"题目类型: {q.question_type}")
    print(f"题目文本: {q.question_text[:50]}...")
    print(f"正确答案: {q.correct_answer}")
    print(f"答案类型: {type(q.correct_answer)}")
    print(f"分数: {q.score}")

db.close()
