"""
仅测试文本分块功能
"""


import sys
import os
# 将 backend 目录放到 sys.path 首位，确保优先使用本地 services 包
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.text_chunker import RecursiveTextChunker


def test_text_chunking():
    """测试文本分块功能"""
    
    print("🔄 开始测试文本分块...")
    
    # 创建分块器
    chunker = RecursiveTextChunker(
        chunk_size=512,
        chunk_overlap=100
    )
    
    # 测试文本
    test_text = """
    人工智能（Artificial Intelligence，AI）是计算机科学的一个分支，
    它企图了解智能的实质，并生产出一种新的能以人类智能相似的方式做出反应的智能机器。
    该领域的研究包括机器人、语言识别、图像识别、自然语言处理和专家系统等。
    
    机器学习是人工智能的一个重要分支，它是一种让计算机系统自动学习和改进的方法，
    无需被明确编程。机器学习算法通过分析大量数据来识别模式，并使用这些模式来做出预测或决策。
    
    深度学习是机器学习的一个子集，它使用人工神经网络来模拟人脑的工作方式。
    深度学习在图像识别、语音识别、自然语言处理等领域取得了显著的成果。
    
    自然语言处理（Natural Language Processing，NLP）是人工智能的一个重要应用领域，
    它致力于让计算机理解、解释和生成人类语言。NLP技术被广泛应用于搜索引擎、
    机器翻译、语音助手、文本分析等领域。
    
    计算机视觉是另一个重要的AI应用领域，它让计算机能够从数字图像或视频中提取、
    分析和理解有用信息。计算机视觉技术在自动驾驶、医学诊断、安防监控、
    工业质检等领域发挥着重要作用。
    """
    
    metadata = {
        "title": "人工智能介绍",
        "category": "technology",
        "author": "测试作者"
    }
    
    try:
        # 1. 测试 token 计算
        total_tokens = chunker.count_tokens(test_text)
        print(f"📊 原文总 token 数: {total_tokens}")
        print(f"📊 原文字符数: {len(test_text)}")
        
        # 2. 测试文本分块
        chunks = chunker.chunk_text(test_text, metadata)
        
        print(f"\n📝 分块结果:")
        print(f"  分块数量: {len(chunks)}")
        
        total_chunk_tokens = 0
        for i, chunk in enumerate(chunks):
            print(f"\n  分块 {i}:")
            print(f"    Token 数: {chunk.token_count}")
            print(f"    字符数: {len(chunk.content)}")
            print(f"    位置: {chunk.start_pos}-{chunk.end_pos}")
            print(f"    内容预览: {chunk.content[:100]}...")
            
            total_chunk_tokens += chunk.token_count
        
        print(f"\n📊 统计信息:")
        print(f"  总分块 tokens: {total_chunk_tokens}")
        print(f"  平均每块 tokens: {total_chunk_tokens / len(chunks):.1f}")
        
        # 3. 检查重叠情况
        if len(chunks) > 1:
            print(f"\n🔗 重叠检查:")
            for i in range(len(chunks) - 1):
                current_end = chunks[i].content[-50:]  # 当前块结尾
                next_start = chunks[i + 1].content[:50]  # 下一块开头
                print(f"  块 {i}-{i+1} 边界:")
                print(f"    当前块结尾: ...{current_end}")
                print(f"    下一块开头: {next_start}...")
        
        print("\n✅ 文本分块测试完成！")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_text_chunking()
    if success:
        print("\n🎉 所有测试通过！")
    else:
        print("\n💥 测试失败！")
        sys.exit(1)