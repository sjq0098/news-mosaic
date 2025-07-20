"""
LangChain 风格文本分块器
"""

import re
import tiktoken
from typing import List, Dict, Any, Optional
from loguru import logger

from models.embedding import TextChunk


class RecursiveTextChunker:
    """递归文本分块器（LangChain 风格）"""
    
    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        encoding_name: str = "cl100k_base"  # GPT-4 编码器
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.encoding = tiktoken.get_encoding(encoding_name)
        
        # 分隔符优先级（从高到低）
        self.separators = [
            "\n\n",  # 段落分隔
            "\n",    # 行分隔
            "。",    # 中文句号
            "！",    # 中文感叹号
            "？",    # 中文问号
            ".",     # 英文句号
            "!",     # 英文感叹号
            "?",     # 英文问号
            ";",     # 分号
            "，",    # 中文逗号
            ",",     # 英文逗号
            " ",     # 空格
            ""       # 字符级别分割
        ]
    
    def count_tokens(self, text: str) -> int:
        """计算文本的 token 数量"""
        try:
            return len(self.encoding.encode(text))
        except Exception as e:
            logger.warning(f"Token 计算失败: {e}，使用字符数估算")
            return len(text) // 4  # 粗略估算：平均每 4 个字符 1 个 token
    
    def chunk_text(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextChunk]:
        """
        递归分块文本
        """
        if metadata is None:
            metadata = {}
        
        # 预处理
        text = self._preprocess_text(text)
        
        # 长度足够小则直接返回
        if self.count_tokens(text) <= self.chunk_size:
            return [TextChunk(
                content=text,
                chunk_index=0,
                token_count=self.count_tokens(text),
                start_pos=0,
                end_pos=len(text),
                metadata={**metadata, "total_chunks": 1}
            )]
        
        # 递归分块
        chunks = self._recursive_split(text, self.separators.copy())
        # 处理重叠合并
        final_chunks = self._merge_chunks_with_overlap(chunks)
        
        # 生成 TextChunk 对象
        result_chunks: List[TextChunk] = []
        char_pos = 0
        for i, c in enumerate(final_chunks):
            start = text.find(c, char_pos)
            if start == -1:
                start = char_pos
            end = start + len(c)
            result_chunks.append(TextChunk(
                content=c,
                chunk_index=i,
                token_count=self.count_tokens(c),
                start_pos=start,
                end_pos=end,
                metadata={
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(final_chunks),
                    "char_start": start,
                    "char_end": end
                }
            ))
            char_pos = end
        
        logger.info(f"文本分块完成：{len(result_chunks)} 个分块")
        return result_chunks
    
    # ---------- 内部辅助方法 ----------
    
    def _preprocess_text(self, text: str) -> str:
        """去除多余空白"""
        return re.sub(r"\s+", " ", text).strip()
    
    def _recursive_split(self, text: str, seps: List[str]) -> List[str]:
        """按优先级递归分割"""
        if not seps:
            return self._character_split(text)
        
        sep = seps[0]
        rest = seps[1:]
        
        if sep == "":
            return self._character_split(text)
        
        parts = text.split(sep)
        if len(parts) > 1:
            parts = [parts[0]] + [sep + p for p in parts[1:]]
        
        results: List[str] = []
        for p in parts:
            if self.count_tokens(p) <= self.chunk_size:
                if p.strip():
                    results.append(p)
            else:
                results.extend(self._recursive_split(p, rest))
        return results
    
    def _character_split(self, text: str) -> List[str]:
        """按字符粗分"""
        res = []
        start = 0
        while start < len(text):
            end = start
            tokens = 0
            while end < len(text) and tokens < self.chunk_size:
                end += 1
                tokens = self.count_tokens(text[start:end])
            if end < len(text):
                while end > start and text[end-1] not in [" ", "\n", "\t"]:
                    end -= 1
                if end == start:
                    end = start + self.chunk_size
            chunk = text[start:end].strip()
            if chunk:
                res.append(chunk)
            start = end
        return res
    
    def _merge_chunks_with_overlap(self, chunks: List[str]) -> List[str]:
        """合并并添加重叠"""
        if not chunks:
            return []
        if len(chunks) == 1:
            return chunks
        
        merged = []
        current = chunks[0]
        for nxt in chunks[1:]:
            combined = current + nxt
            if self.count_tokens(combined) <= self.chunk_size:
                current = combined
            else:
                merged.append(current)
                if self.chunk_overlap > 0:
                    overlap = self._get_overlap_text(current, self.chunk_overlap)
                    current = overlap + nxt
                else:
                    current = nxt
        merged.append(current)
        return merged
    
    def _get_overlap_text(self, text: str, overlap_tokens: int) -> str:
        """取结尾 overlap_tokens 大小的文本"""
        if overlap_tokens <= 0:
            return ""
        words = text.split()
        if not words:
            return ""
        
        overlap_words = []
        cur_tokens = 0
        for w in reversed(words):
            overlap_words.insert(0, w)
            cur_tokens = self.count_tokens(" ".join(overlap_words))
            if cur_tokens >= overlap_tokens:
                break
        return " ".join(overlap_words)