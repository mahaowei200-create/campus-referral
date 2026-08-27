from pathlib import Path
from types import SimpleNamespace

from app.services.knowledge import bm25_scores, chunk_text


def load_campus_resource_chunks():  #校园资源
    project_root = Path(__file__).resolve().parents[1]
    knowledge_file = (
        project_root
        / "app"
        / "knowledge"
        / "campus-referral-resources.md"
    )

    content = knowledge_file.read_text(encoding="utf-8")  #阅读markdown文件
    pieces = chunk_text(content, size=512, overlap=64)  #把整篇很长的 md 文档，切割成**多段小文本块 (chunk)**，每块最大 512 字符；

    return [
        SimpleNamespace(id=index, content=piece)  #SimpleNamespace 模拟数据库对象
        for index, piece in enumerate(pieces, start=1)
    ]


def find_best_chunk(query: str):  #输入用户问题，返回相关性最高的知识库文本块。
    chunks = load_campus_resource_chunks()
    scores = bm25_scores(query, chunks)

    assert scores

    best_chunk_id = max(scores, key=scores.get)  #拿到分数字典里分数最大的那个 chunk id。

    return next(   #根据 id 遍历找到对应的 chunk 对象，返回这个最匹配的文本片段。
        chunk
        for chunk in chunks
        if chunk.id == best_chunk_id
    )


def test_retrieve_academic_affairs_resource():
    best_chunk = find_best_chunk("补考、选课和学分问题应该找谁")

    assert "教务处" in best_chunk.content
    assert "补考" in best_chunk.content


def test_retrieve_career_center_resource():
    best_chunk = find_best_chunk("我想找实习，需要修改简历并准备招聘面试")

    assert "就业指导中心" in best_chunk.content
    assert "实习" in best_chunk.content


def test_retrieve_financial_aid_resource():
    best_chunk = find_best_chunk("家庭经济困难，怎么申请助学金和助学贷款")

    assert "学生资助中心" in best_chunk.content
    assert "助学金" in best_chunk.content


def test_retrieve_psychological_center_resource():
    best_chunk = find_best_chunk("最近总是焦虑失眠，情绪也很低落")

    assert "心理咨询中心" in best_chunk.content
    assert "焦虑" in best_chunk.content


def test_retrieve_campus_security_resource():
    best_chunk = find_best_chunk("我在学校被人跟踪威胁，还遭到了校园欺凌")

    assert "校园保卫处" in best_chunk.content
    assert "校园欺凌" in best_chunk.content
