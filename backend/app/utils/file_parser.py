"""
文件解析工具
支持PDF、Markdown、TXT文件的文本提取
"""

from pathlib import Path
from typing import List


def _read_text_with_fallback(file_path: str) -> str:
    """
    读取文本文件，UTF-8失败时自动探测编码。
    
    采用多级回退策略：
    1. 首先尝试 UTF-8 解码
    2. 使用 charset_normalizer 检测编码
    3. 回退到 chardet 检测编码
    4. 最终使用 UTF-8 + errors='replace' 兜底
    
    Args:
        file_path: 文件路径
        
    Returns:
        解码后的文本内容
    """
    data = Path(file_path).read_bytes()
    
    # 首先尝试 UTF-8
    try:
        return data.decode('utf-8')
    except UnicodeDecodeError:
        pass
    
    # 尝试使用 charset_normalizer 检测编码
    encoding = None
    try:
        from charset_normalizer import from_bytes
        best = from_bytes(data).best()
        if best and best.encoding:
            encoding = best.encoding
    except Exception:
        pass
    
    # 回退到 chardet
    if not encoding:
        try:
            import chardet
            result = chardet.detect(data)
            encoding = result.get('encoding') if result else None
        except Exception:
            pass
    
    # 最终兜底：使用 UTF-8 + replace
    if not encoding:
        encoding = 'utf-8'
    
    return data.decode(encoding, errors='replace')


class FileParser:
    """文件解析器"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.md', '.markdown', '.txt'}
    
    @classmethod
    def extract_text(cls, file_path: str) -> str:
        """
        从文件中提取文本
        
        Args:
            file_path: 文件路径
            
        Returns:
            提取的文本内容
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        suffix = path.suffix.lower()
        
        if suffix not in cls.SUPPORTED_EXTENSIONS:
            raise ValueError(f"不支持的文件格式: {suffix}")
        
        if suffix == '.pdf':
            return cls._extract_from_pdf(file_path)
        elif suffix in {'.md', '.markdown'}:
            return cls._extract_from_md(file_path)
        elif suffix == '.txt':
            return cls._extract_from_txt(file_path)
        
        raise ValueError(f"无法处理的文件格式: {suffix}")
    
    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        """从PDF提取文本"""
        try:
            import fitz  # PyMuPDF
        except ImportError as e:
            raise ImportError("需要安装PyMuPDF: pip install PyMuPDF") from e
        
        text_parts = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)
        
        return "\n\n".join(text_parts)
    
    @staticmethod
    def _extract_from_md(file_path: str) -> str:
        """从Markdown提取文本，支持自动编码检测"""
        return _read_text_with_fallback(file_path)
    
    @staticmethod
    def _extract_from_txt(file_path: str) -> str:
        """从TXT提取文本，支持自动编码检测"""
        return _read_text_with_fallback(file_path)
    
    @classmethod
    def extract_from_multiple(cls, file_paths: List[str]) -> str:
        """
        从多个文件提取文本并合并
        
        Args:
            file_paths: 文件路径列表
            
        Returns:
            合并后的文本
        """
        all_texts = []
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                text = cls.extract_text(file_path)
                filename = Path(file_path).name
                all_texts.append(f"=== 文档 {i}: {filename} ===\n{text}")
            except Exception as e:
                all_texts.append(f"=== 文档 {i}: {file_path} (提取失败: {str(e)}) ===")
        
        return "\n\n".join(all_texts)


_CHUNK_SEPARATORS = ('。', '！', '？', '.\n', '!\n', '?\n', '\n\n', '. ', '! ', '? ')


def split_text_into_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[str]:
    """将文本按 chunk_size 切块，块间保留 overlap 个字符用于上下文。

    相比之前的实现：
    - 使用 str.rfind(sep, start, end) 在原串上做切分，省去每轮的 text[start:end]
      子串拷贝，避免在长文本上产生 O(n·k) 的额外内存/时间
    - 显式钳制 overlap < chunk_size 并保证每轮至少前进 1 字符，杜绝曾经的
      overlap >= chunk_size 导致死循环的隐患
    - 提取句子分隔符为常量元组，避免每次进入循环都重新构造列表

    Args:
        text: 原始文本
        chunk_size: 每块的字符数（必须 > 0）
        overlap: 相邻块之间的重叠字符数（会被钳制到 [0, chunk_size - 1]）

    Returns:
        文本块列表（strip 后非空）
    """
    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")
    # overlap 必须严格小于 chunk_size，否则 start 永远不会推进
    if overlap < 0:
        overlap = 0
    if overlap >= chunk_size:
        overlap = chunk_size - 1

    n = len(text)
    if n <= chunk_size:
        return [text] if text.strip() else []

    chunks: List[str] = []
    start = 0
    min_split_offset = int(chunk_size * 0.3)

    while start < n:
        end = start + chunk_size

        if end < n:
            # 在 [start, end) 区间内就近向后对齐到句子边界。rfind 接受 start/end
            # 参数，直接在原串上搜索（无需切片拷贝）。返回值是原串索引，不是
            # 子串内的相对偏移。
            for sep in _CHUNK_SEPARATORS:
                sep_idx = text.rfind(sep, start, end)
                if sep_idx != -1 and sep_idx - start > min_split_offset:
                    end = sep_idx + len(sep)
                    break
        else:
            end = n

        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)

        if end >= n:
            break

        # 下一轮起点：至少前进 1 字符，防止因分隔符紧贴 start 而卡死
        next_start = end - overlap
        if next_start <= start:
            next_start = start + 1
        start = next_start

    return chunks

