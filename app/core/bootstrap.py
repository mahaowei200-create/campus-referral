from pathlib import Path

from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.security import hash_password
from app.models.entities import UserAccount
from app.services.knowledge import KnowledgeService

#数据库不存在对应表 → 自动新建表
def create_schema() -> None:
    Base.metadata.create_all(bind=engine)


def seed_data(db: Session) -> None:
    if db.query(UserAccount).count() == 0:
        admin = UserAccount(
            username="admin",
            display_name="Counselor Admin",
            password_hash=hash_password("admin123"),
        )
        admin.roles = {"ROLE_ADMIN", "ROLE_USER"}
        student = UserAccount(
            username="student",
            display_name="Demo Student",
            password_hash=hash_password("student123"),
        )
        student.roles = {"ROLE_USER"}   
        db.add_all([admin, student])
        db.commit()

    service = KnowledgeService(db, get_settings())   
    root = Path(__file__).resolve().parents[1]
    for file in sorted((root / "knowledge").glob("*.md")):     #查看knowledge目录下的所有md文件，并且按文件名排序
        service.ensure_source(file.name, file.read_text(encoding="utf-8")) #确保源存在，如果不存在则创建，存在则返回源ID
