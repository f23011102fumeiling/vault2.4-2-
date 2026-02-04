from app.database import SessionLocal
from app.models.survey import Question, Survey

db = SessionLocal()

# 查询所有填空题
fill_blank_questions = db.query(Question).filter(Question.question_type == 'fill_blank').all()

print(f"找到 {len(fill_blank_questions)} 道填空题:")
for q in fill_blank_questions:
    print(f"\n题目ID: {q.id}")
    print(f"题目文本: {q.question_text[:50]}...")
    print(f"正确答案: {q.correct_answer}")
    print(f"答案类型: {type(q.correct_answer)}")
    print(f"分数: {q.score}")

db.close()
