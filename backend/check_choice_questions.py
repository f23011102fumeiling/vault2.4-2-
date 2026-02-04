from app.database import SessionLocal
from app.models.survey import Question, Survey

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
    print(f"选项: {q.options}")
    print(f"选项类型: {type(q.options)}")
    if q.options:
        print(f"选项长度: {len(q.options) if isinstance(q.options, list) else 'N/A'}")
        if isinstance(q.options, list) and len(q.options) > 0:
            print(f"第一个选项: {q.options[0]}, 类型: {type(q.options[0])}")

db.close()
