from app.services.knowledge import SearchResult
from app.services.campus_resource import CampusResourceRetriever


class FakeKnowledgeService:
    def __init__(self, results):
        self.results = results
        self.received_query = None
        self.received_top_k = None

    def retrieve(self, query: str, top_k: int):
        self.received_query = query
        self.received_top_k = top_k

        return self.results[:top_k]


def test_retriever_calls_knowledge_service():
    fake_service = FakeKnowledgeService(
        results=[
            SearchResult(
                chunk_id=1,
                source="campus-referral-resources.md",
                content="教务处主要处理补考、选课和学分问题。",
                score=0.95,
            )
        ]
    )

    retriever = CampusResourceRetriever(fake_service)

    results = retriever.retrieve(
        query="补考应该找哪个部门",
        top_k=1,
    )

    assert fake_service.received_query == "补考应该找哪个部门"
    assert fake_service.received_top_k == 1
    assert len(results) == 1
    assert results[0].source == "campus-referral-resources.md"
    assert "教务处" in results[0].content

def test_build_context_formats_search_results():
    fake_service = FakeKnowledgeService(
        results=[
            SearchResult(
                chunk_id=1,
                source="campus-referral-resources.md",
                content="教务处主要处理补考、选课和学分问题。",
                score=0.95,
            ),
            SearchResult(
                chunk_id=2,
                source="campus-referral-resources.md",
                content="咨询时建议准备学号和课程信息。",
                score=0.82,
            ),
        ]
    )

    retriever = CampusResourceRetriever(fake_service)

    context = retriever.build_context(
        query="补考应该找哪个部门",
        top_k=2,
    )

    assert "[资料1" in context
    assert "[资料2" in context
    assert "来源：campus-referral-resources.md" in context
    assert "教务处主要处理补考" in context
    assert "咨询时建议准备学号" in context

def test_build_context_returns_empty_when_no_results():
    fake_service = FakeKnowledgeService(results=[])

    retriever = CampusResourceRetriever(fake_service)

    context = retriever.build_context(
        query="一个知识库中没有覆盖的问题",
        top_k=3,
    )

    assert context == ""