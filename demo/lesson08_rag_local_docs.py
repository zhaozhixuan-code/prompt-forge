"""第八课：本地文档 RAG。

RAG = Retrieval Augmented Generation，检索增强生成。

本课只实现最小链路，不引入向量数据库：
1. 从本地读取项目文档。
2. 把文档切成小片段。
3. 用关键词做一个内存检索器。
4. 把命中的片段作为上下文交给模型。
5. 要求模型只能基于上下文回答。

这个 demo 的重点是理解 RAG 数据流，不是构建生产级检索系统。
"""

from dataclasses import dataclass
from pathlib import Path

from langchain_core.prompts import ChatPromptTemplate

from app.ai.model_client import create_chat_model
from app.core.config import PROJECT_ROOT, get_settings


@dataclass
class DocumentChunk:
    """本地文档切片。"""

    # source 记录片段来自哪个文件，方便回答时展示来源。
    source: str
    # index 是片段在该文件内的序号，便于定位和调试。
    index: int
    # content 是实际会提供给模型的文档内容。
    content: str


def load_local_documents() -> list[DocumentChunk]:
    """读取本地项目文档并切分成片段。"""

    # 这里选择 AGENTS.md 和重构指南，是因为它们包含项目约束、接口约定、
    # 技术栈和迁移目标，适合演示“让模型基于项目文档回答”。
    paths = [
        PROJECT_ROOT / "AGENTS.md",
        PROJECT_ROOT / "docs" / "python-backend-refactor-guide.md",
    ]
    chunks: list[DocumentChunk] = []
    for path in paths:
        if not path.exists():
            continue

        # errors="ignore" 可以避免个别异常字符导致整个 demo 读取失败。
        text = path.read_text(encoding="utf-8", errors="ignore")

        # 最小切分策略：按空行切段。
        # 生产 RAG 通常会用更稳定的 splitter，并控制 chunk size / overlap。
        paragraphs = [item.strip() for item in text.split("\n\n") if item.strip()]
        for index, paragraph in enumerate(paragraphs):
            chunks.append(
                DocumentChunk(
                    source=str(path.relative_to(PROJECT_ROOT)),
                    index=index,
                    # 限制单个 chunk 长度，避免把过长上下文塞给模型。
                    content=paragraph[:1200],
                )
            )
    return chunks


def _query_terms(question: str) -> set[str]:
    """提取简单检索关键词。"""

    # 这里不是中文分词器，只是最小可读实现：
    # - 先做小写和符号替换。
    # - 再用空格拆英文/符号关键词。
    # - 对中文场景补充少量项目领域词。
    normalized = (
        question.lower()
        .replace("/", " ")
        .replace("_", " ")
        .replace("-", " ")
        .replace("，", " ")
        .replace("。", " ")
    )
    terms = {term for term in normalized.split() if len(term) >= 2}

    # 常见技术关键词：如果问题里出现，就加入检索词集合。
    for keyword in ["fastapi", "redis", "mysql", "langchain", "sse", "api", "health"]:
        if keyword in normalized:
            terms.add(keyword)

    # 针对本项目文档里的精确符号做增强。
    # 例如用户问“API 前缀”，文档里实际写的是 `/api`。
    if "前缀" in question or "api" in normalized:
        terms.add("/api")
    if "健康" in question or "health" in normalized:
        terms.add("/api/health")
        terms.add("health")
    return terms


def retrieve(question: str, chunks: list[DocumentChunk], top_k: int = 3) -> list[DocumentChunk]:
    """使用关键词重叠实现最小内存检索器。"""

    terms = _query_terms(question)
    scored: list[tuple[int, DocumentChunk]] = []
    for chunk in chunks:
        content_lower = chunk.content.lower()

        # 基础得分：问题关键词命中文档片段的数量。
        score = sum(1 for term in terms if term in content_lower)

        # 精确接口路径对本项目更重要，所以给额外权重。
        # 这样问 `/api/health` 时，会优先命中真正包含接口路径的片段。
        for symbol in ["/api/health", "/api"]:
            if symbol in terms and symbol in content_lower:
                score += 3
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: item[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def answer_with_local_docs(question: str) -> str:
    """基于检索到的本地文档回答问题。"""

    # RAG 第一步：加载知识库。
    chunks = load_local_documents()

    # RAG 第二步：根据用户问题检索相关片段。
    hits = retrieve(question, chunks)
    if not hits:
        return "没有检索到相关本地文档片段。"

    # RAG 第三步：把命中的片段拼成上下文。
    # 每个片段带 source#index，方便回答后检查来源。
    context = "\n\n".join(
        f"[{chunk.source}#{chunk.index}]\n{chunk.content}" for chunk in hits
    )
    sources = "\n".join(f"- {chunk.source}#{chunk.index}" for chunk in hits)

    settings = get_settings()
    if not settings.resolved_ai_api_key:
        # 没有模型 key 时仍然输出命中的上下文，便于学习检索阶段。
        return f"请先在 .env 中配置 AI_API_KEY。\n\n=== 命中文档 ===\n{sources}\n\n{context}"

    model = create_chat_model(settings)

    # RAG 第四步：把检索上下文注入 prompt。
    # system prompt 明确要求“只能根据文档片段回答”，降低模型编造概率。
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", "你只能根据给定的项目文档片段回答，不能编造。"),
            ("human", "问题：{question}\n\n项目文档片段：\n{context}"),
        ]
    )

    # RAG 第五步：生成回答。
    response = (prompt | model).invoke({"question": question, "context": context})
    return f"=== 命中文档 ===\n{sources}\n\n=== 回答 ===\n{response.content}"


def main() -> None:
    """运行本课 demo。"""

    question = "PromptForge 的 API 前缀和健康检查接口是什么？"
    print(answer_with_local_docs(question))


if __name__ == "__main__":
    main()
