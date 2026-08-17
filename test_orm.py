from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# 核心：直接从实体文件导入，不经过app.models导出，不会报找不到类
from app.models.entities import Base, UserAccount, ChatSession,ChatMessage

# 使用内存SQLite，不需要本地数据库文件，纯mock测试
engine = create_engine("sqlite:///:memory:", echo=True)
SessionLocal = sessionmaker(bind=engine)

# 自动根据entities里的模型创建全部数据表
Base.metadata.create_all(bind=engine)
print("===== 数据表创建完成 =====")

# 测试新增用户数据
db = SessionLocal()
test_user = UserAccount(
    username="test_user001",
    password_hash="12345678",
    display_name="测试用户",
    roles_csv="user",
    created_at=datetime(2026, 6, 24, 11, 33, 20)
)
db.add(test_user)
db.commit()

# 查询打印数据，验证ORM正常工作
user_list = db.query(UserAccount).all()
print("查询到的用户数据：", user_list)

db.close()
print("===== 测试执行完毕 =====")


# 1. 新增一个会话
from datetime import datetime
session1 = ChatSession(
    user_id=1,
    created_at=datetime.now()
)
db.add(session1)
db.commit()

# 2. 给这个会话插入两条消息
msg1 = ChatMessage(session_id=session1.id, content="你好")
msg2 = ChatMessage(session_id=session1.id, content="帮我分析情绪")
db.add_all([msg1, msg2])
db.commit()

# ========== relationship 演示 ==========
# 正向：从消息找所属会话
msg = db.query(ChatMessage).first()
print("消息所属会话ID：", msg.session.id)
print("会话所属用户ID：", msg.session.user_id)

# 反向：从会话一次性取出所有消息（不用写JOIN SQL）
session_obj = db.query(ChatSession).get(1)
print("该会话全部消息：", [m.content for m in session_obj.messages])