from app.services.knowledge import KnowledgeService, SearchResult


class CampusResourceRetriever:
    def __init__(self, knowledge_service: KnowledgeService):
        self.knowledge_service = knowledge_service

    def retrieve(self, query: str,top_k: int = 3) -> list[SearchResult]: #向量检索
        normalized_query = query.strip()

        if not normalized_query:
            return []

        safe_top_k = max(1, top_k)

        return self.knowledge_service.retrieve(
            query=normalized_query,
            top_k=safe_top_k,
        )

    def build_context(self, query: str, top_k: int = 3,) -> str: #构建上下文
        results = self.retrieve(
            query=query,
            top_k=top_k,
        )

        if not results:
            return ""

        sections = []

        for index, result in enumerate(results, start=1):
            content = result.content.strip()

            if not content:
                continue

            source = result.source or "未知来源"

            section = (
                f"[资料{index}｜来源：{source}]\n"
                f"{content}"
            )

            sections.append(section)

        return "\n\n".join(sections)