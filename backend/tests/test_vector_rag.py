import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.embedding_service import embedding_service
from services.vector_db_service import get_vector_db
from models.embedding import EmbeddingResult

sample_docs = [
    {
        "news_id": "news_1",
        "title": "AI 公司完成 1 亿美元融资",
        "body": "今天，一家从事 AIGC 的初创公司宣布完成 1 亿美元 A 轮融资，由知名基金领投……",
        "published_at": "2025-07-15"
    },
    {
        "news_id": "news_2",
        "title": "AI 芯片市场迎来爆发式增长",
        "body": "随着生成式 AI 的普及，AI 专用芯片需求激增，市场规模有望在三年内翻番……",
        "published_at": "2025-07-14"
    }
]


async def build_embeddings():
    texts = [d["body"] for d in sample_docs]
    ids = [d["news_id"] for d in sample_docs]
    metas = [{"title": d["title"], "published_at": d["published_at"]} for d in sample_docs]

    results_nested = await embedding_service.process_texts_batch(texts, ids, metas)
    # process_texts_batch 返回 List[List[EmbeddingResult]]
    flat: list[EmbeddingResult] = [r for sub in results_nested for r in sub]
    return flat


async def main():
    vec_db = get_vector_db()

    emb_results = await build_embeddings()
    vec_db.upsert_embeddings(emb_results)

    query = "哪家公司获得了 1 亿美元融资？"
    hits = vec_db.query_similar(query, top_k=3)

    assert hits, "检索结果为空"
    print("检索结果：")
    for h in hits:
        print(h["news_id"], h["score"], h["metadata"].get("title"))


if __name__ == "__main__":
    asyncio.run(main()) 