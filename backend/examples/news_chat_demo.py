"""
新闻对话功能演示
展示RAG增强的智能新闻分析对话
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any
import sys
import os

# 添加路径
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

try:
    from models.news import NewsModel, NewsSource, NewsCategory
    from services.news_chat_service import NewsChatService
except ImportError as e:
    print(f"导入错误: {e}")
    print("这是一个演示脚本，实际运行需要完整的服务环境")
    sys.exit(1)


class NewsChatDemo:
    """新闻对话演示"""
    
    def __init__(self):
        self.chat_service = NewsChatService()
        self.demo_news = self._create_demo_news()
    
    def _create_demo_news(self) -> Dict[str, NewsModel]:
        """创建演示新闻"""
        return {
            "ai_breakthrough": NewsModel(
                id="demo_ai_001",
                title="中国AI大模型在国际评测中获得突破性成绩",
                summary="国产大语言模型在多项国际基准测试中超越GPT-4，标志着中国AI技术达到世界领先水平",
                content="""
                近日，中国自主研发的大语言模型"天工3.0"在Stanford HAI发布的HELM评测、
                OpenAI的Evals基准测试等多项国际权威评估中取得突破性成绩。
                
                在逻辑推理、代码生成、多语言理解等核心能力测试中，天工3.0的表现
                超越了GPT-4、Claude等国际先进模型。特别是在中文语言处理和
                中华文化理解方面，显示出显著优势。
                
                该模型采用了创新的混合专家架构，参数规模达到1.8万亿，
                训练数据涵盖100多种语言，支持32K上下文长度。
                
                业界专家认为，这一突破标志着中国在AI核心技术领域实现了
                从跟随到并跑再到领跑的历史性跨越。
                """,
                url="https://example.com/news/ai-breakthrough-2024",
                source=NewsSource.MANUAL,
                category=NewsCategory.TECHNOLOGY,
                keywords=["AI大模型", "技术突破", "国际评测", "自主研发"],
                published_at=datetime.utcnow()
            ),
            
            "economic_growth": NewsModel(
                id="demo_eco_001",
                title="三季度GDP同比增长5.2%，经济复苏势头强劲",
                summary="最新数据显示中国经济持续恢复，消费、投资、出口三驾马车协调发力",
                content="""
                国家统计局今日发布数据显示，第三季度国内生产总值(GDP)同比增长5.2%，
                高于市场预期的4.9%，显示中国经济复苏势头强劲。
                
                分产业看，第一产业增加值同比增长4.0%，第二产业增长4.7%，
                第三产业增长5.8%。消费对经济增长的贡献率达到65.3%。
                
                制造业投资增长6.2%，高技术产业投资增长11.4%，
                显示经济结构持续优化。进出口贸易稳中有进，
                对"一带一路"沿线国家进出口增长8.1%。
                
                专家分析认为，随着政策效果显现和市场信心恢复，
                全年经济增长目标有望顺利实现。
                """,
                url="https://example.com/news/gdp-growth-2024",
                source=NewsSource.MANUAL,
                category=NewsCategory.BUSINESS,
                keywords=["GDP增长", "经济复苏", "消费增长", "投资数据"],
                published_at=datetime.utcnow()
            )
        }
    
    async def run_complete_demo(self):
        """运行完整演示"""
        print("🎯 新闻智能对话系统演示")
        print("=" * 50)
        
        # 场景1：创建会话并分析首条新闻
        await self._demo_initial_analysis()
        
        # 场景2：深度追问对话
        await self._demo_follow_up_conversation()
        
        # 场景3：添加新新闻进行对比
        await self._demo_news_comparison()
        
        # 场景4：趋势预测讨论
        await self._demo_trend_prediction()
        
        # 场景5：相关新闻检索
        await self._demo_related_news()
        
        print("\n✅ 演示完成")
        print("=" * 50)
    
    async def _demo_initial_analysis(self):
        """演示初始新闻分析"""
        print("\n📰 场景1：初始新闻分析")
        print("-" * 30)
        
        # 创建会话
        session = await self.chat_service.create_news_session(
            user_id="demo_user",
            initial_news=self.demo_news["ai_breakthrough"],
            session_title="AI突破新闻分析"
        )
        
        print(f"✅ 创建会话: {session.id}")
        
        # 获取初始分析
        messages = self.chat_service._messages.get(session.id, [])
        if messages:
            welcome_msg = messages[-1]
            print(f"\n🤖 AI分析:")
            print(f"📝 {welcome_msg.content}")
            
            if "suggested_questions" in welcome_msg.metadata:
                print(f"\n💡 建议问题:")
                for i, q in enumerate(welcome_msg.metadata["suggested_questions"], 1):
                    print(f"   {i}. {q}")
        
        return session.id
    
    async def _demo_follow_up_conversation(self):
        """演示追问对话"""
        print("\n💬 场景2：深度追问对话")
        print("-" * 30)
        
        # 创建新会话
        session = await self.chat_service.create_news_session(
            user_id="demo_user",
            initial_news=self.demo_news["ai_breakthrough"]
        )
        
        # 模拟用户追问
        follow_up_questions = [
            "这个技术突破对中国AI产业有什么具体影响？",
            "与GPT-4相比，具体在哪些方面表现更好？",
            "未来这项技术可能面临哪些挑战？"
        ]
        
        for question in follow_up_questions:
            print(f"\n👤 用户: {question}")
            
            response = await self.chat_service.send_news_message(
                session_id=session.id,
                user_message=question
            )
            
            print(f"🤖 AI回复:")
            print(f"📝 {response['assistant_message']['content'][:200]}...")
            
            if response.get("suggested_questions"):
                print(f"💡 新建议: {response['suggested_questions'][0]}")
    
    async def _demo_news_comparison(self):
        """演示新闻对比分析"""
        print("\n🔄 场景3：新闻对比分析")
        print("-" * 30)
        
        # 创建会话
        session = await self.chat_service.create_news_session(
            user_id="demo_user",
            initial_news=self.demo_news["ai_breakthrough"]
        )
        
        # 添加第二条新闻进行对比
        print("👤 用户: 我想分析另一条关于经济的新闻，并与AI新闻进行对比")
        
        response = await self.chat_service.send_news_message(
            session_id=session.id,
            user_message="请分析这条经济新闻，并与之前的AI新闻进行对比",
            news_data=self.demo_news["economic_growth"]
        )
        
        print(f"🤖 AI对比分析:")
        print(f"📝 {response['assistant_message']['content'][:300]}...")
        
        # 进一步对比讨论
        print(f"\n👤 用户: 这两条新闻反映了什么共同趋势？")
        
        comparison_response = await self.chat_service.send_news_message(
            session_id=session.id,
            user_message="这两条新闻反映了什么共同趋势？"
        )
        
        print(f"🤖 趋势分析:")
        print(f"📝 {comparison_response['assistant_message']['content'][:200]}...")
    
    async def _demo_trend_prediction(self):
        """演示趋势预测"""
        print("\n📈 场景4：趋势预测分析")
        print("-" * 30)
        
        session = await self.chat_service.create_news_session(
            user_id="demo_user",
            initial_news=self.demo_news["ai_breakthrough"]
        )
        
        print("👤 用户: 基于这个AI突破，请预测未来一年的发展趋势")
        
        response = await self.chat_service.send_news_message(
            session_id=session.id,
            user_message="基于这个AI突破，请预测未来一年的发展趋势"
        )
        
        print(f"🤖 趋势预测:")
        print(f"📝 {response['assistant_message']['content'][:300]}...")
        
        print(f"🏷️  分析类型: {response['assistant_message']['metadata'].get('analysis_type')}")
    
    async def _demo_related_news(self):
        """演示相关新闻检索"""
        print("\n🔍 场景5：相关新闻检索")
        print("-" * 30)
        
        session = await self.chat_service.create_news_session(
            user_id="demo_user",
            initial_news=self.demo_news["ai_breakthrough"]
        )
        
        print("👤 用户: 能帮我找一些与AI技术相关的其他新闻吗？")
        
        try:
            response = await self.chat_service.send_news_message(
                session_id=session.id,
                user_message="能帮我找一些与AI技术相关的其他新闻吗？"
            )
            
            print(f"🤖 相关新闻:")
            print(f"📝 {response['assistant_message']['content'][:250]}...")
            
            if "related_count" in response['assistant_message']['metadata']:
                count = response['assistant_message']['metadata']['related_count']
                print(f"📊 找到 {count} 条相关新闻")
                
        except Exception as e:
            print(f"⚠️  相关新闻检索需要向量数据库支持: {e}")
    
    async def _demo_context_tracking(self):
        """演示上下文跟踪"""
        print("\n🧠 上下文跟踪演示")
        print("-" * 30)
        
        session = await self.chat_service.create_news_session(
            user_id="demo_user",
            initial_news=self.demo_news["ai_breakthrough"]
        )
        
        # 发送几轮对话
        await self.chat_service.send_news_message(
            session_id=session.id,
            user_message="这个技术有什么创新点？"
        )
        
        await self.chat_service.send_news_message(
            session_id=session.id,
            user_message="对普通用户有什么影响？"
        )
        
        # 检查上下文
        context = self.chat_service._get_context_summary(session.id)
        print(f"📊 会话统计:")
        print(f"   - 分析新闻数量: {context['analyzed_news_count']}")
        print(f"   - 当前讨论: {context['current_news_title']}")
        
        # 获取会话历史
        history = await self.chat_service.get_session_history(session.id)
        print(f"   - 总消息数: {len(history['messages'])}")
    
    def _format_analysis_summary(self, analysis: Dict[str, Any]) -> str:
        """格式化分析摘要"""
        content = analysis.get("content", "")
        if len(content) > 150:
            content = content[:150] + "..."
        
        metadata = analysis.get("metadata", {})
        analysis_type = metadata.get("analysis_type", "general")
        
        return f"[{analysis_type}] {content}"


async def main():
    """主函数"""
    print("🚀 启动新闻智能对话演示...")
    
    demo = NewsChatDemo()
    
    try:
        await demo.run_complete_demo()
        
        # 额外演示：上下文跟踪
        await demo._demo_context_tracking()
        
    except Exception as e:
        print(f"❌ 演示出错: {e}")
        print("💡 这可能是因为缺少依赖服务（QWEN API、向量数据库等）")


if __name__ == "__main__":
    asyncio.run(main()) 