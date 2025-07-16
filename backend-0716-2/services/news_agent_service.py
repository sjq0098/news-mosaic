"""
智能新闻助手服务 - 基于 LangGraph 的智能新闻搜索系统
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_community.chat_models import ChatTongyi
from langchain.schema import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, END

from core.config import settings
from services.news_service import get_news_service
from services.memory_mongo import SessionMemoryStore
from services.user_interest_service import add_user_interests, remove_user_interests, get_user_interests
from models.news import NewsSearchRequest
from models.agent import AgentState

logger = logging.getLogger(__name__)


class NewsAgentService:
    """智能新闻助手 - 专注新闻搜索和兴趣管理"""
    
    # 分类系统提示词
    CLASSIFY_PROMPT = """你是一名新闻搜索助手，用户接下来会提供一个请求，可能是带有关键词的明确的新闻请求（比如：我想知道今天关于AI有什么新闻？ 或者 我比较感兴趣最近篮球和足球的比赛）；也可能是一个泛泛的新闻请求（比如：查看今日新闻 或者 最近有啥大事？）；也可能是兴趣变化的请求（比如：我最近对科技不感兴趣了 或者 我最近很喜欢汽车）；也可能不是新闻请求（比如：你好 或者 1+3=？ 或者 其他的各种输入） 你需要对输入进行分类，只能回答 准确搜索 、含糊搜索、兴趣调整或其它四者中的一个"""
    
    # 关键词提取提示词
    EXTRACT_KEYWORDS_PROMPT = """从用户的新闻搜索请求中提取关键词。请只输出关键词，用逗号分隔，不要其他内容。最多3个关键词。如果无法提取有效关键词，输出"无"。"""
    
    # 兴趣调整提示词
    INTEREST_INTENT_PROMPT = """分析用户的兴趣调整意图。用户的输入表达了对某些主题的兴趣变化。请分析并回答：
1. 操作类型：增加、删除、查看（只选一个）
2. 涉及主题：具体的兴趣领域关键词（用逗号分隔）

格式：操作类型|主题关键词
例如：增加|科技,AI
如果无法确定，回答：无法确定|无"""

    def __init__(self):
        """初始化智能体服务"""
        self.llm = ChatTongyi(
            streaming=True,
            name="qwen-turbo", 
            dashscope_api_key=settings.DASHSCOPE_API_KEY
        )
        self.memory_store = SessionMemoryStore()
        self.graph = self._build_graph()
        logger.info("智能新闻助手服务初始化完成")
    
    def _build_graph(self) -> StateGraph:
        """构建 LangGraph 工作流"""
        workflow = StateGraph(AgentState)
        
        # 添加节点
        workflow.add_node("load_memory", self._load_memory)
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("extract_keywords", self._extract_keywords)
        workflow.add_node("search_precise", self._search_precise)
        workflow.add_node("search_general", self._search_general)
        workflow.add_node("manage_interests", self._manage_interests)
        workflow.add_node("handle_other", self._handle_other)
        workflow.add_node("save_memory", self._save_memory)
        
        # 设置入口点
        workflow.set_entry_point("load_memory")
        
        # 添加边
        workflow.add_edge("load_memory", "classify_intent")
        
        # 条件路由：根据意图分类
        workflow.add_conditional_edges(
            "classify_intent",
            self._route_by_intent,
            {
                "准确搜索": "extract_keywords",
                "含糊搜索": "search_general",
                "兴趣调整": "manage_interests",
                "其它": "handle_other"
            }
        )
        
        # 准确搜索流程
        workflow.add_edge("extract_keywords", "search_precise")
        workflow.add_edge("search_precise", "save_memory")
        
        # 其他路径直接到保存记忆
        workflow.add_edge("search_general", "save_memory")
        workflow.add_edge("manage_interests", "save_memory")
        workflow.add_edge("handle_other", "save_memory")
        workflow.add_edge("save_memory", END)
        
        return workflow.compile()
    
    async def process_user_message(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        """处理用户消息的主入口"""
        try:
            logger.info(f"处理用户消息 [用户: {user_id}, 会话: {session_id}]: {message}")
            
            # 初始化状态
            initial_state = AgentState(
                messages=[HumanMessage(content=message)],
                user_id=user_id,
                session_id=session_id,
                user_preferences=None,
                extracted_keywords=[],
                search_result=None,
                response_type="",
                interest_operation=None,
                interests_to_manage=[]
            )
            
            # 运行工作流
            final_state = await self.graph.ainvoke(initial_state)
            
            # 提取响应
            last_message = final_state["messages"][-1]
            response_content = last_message.content if hasattr(last_message, 'content') else str(last_message)
            
            return {
                "reply": response_content,
                "type": final_state.get("response_type", "unknown"),
                "keywords_used": final_state.get("extracted_keywords", []),
                "search_result": final_state.get("search_result")
            }
            
        except Exception as e:
            logger.error(f"处理用户消息失败: {str(e)}")
            return {
                "reply": "抱歉，处理您的请求时遇到了问题，请稍后重试。",
                "type": "error",
                "error": str(e)
            }
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            # 简单的LLM连接测试
            test_msg = [HumanMessage(content="test")]
            await self.llm.ainvoke(test_msg)
            return True
        except:
            return False
    
    async def _load_memory(self, state: AgentState) -> AgentState:
        """载入会话记忆 - 暂时禁用记忆载入避免干扰当前对话"""
        try:
            # 记忆载入功能暂时禁用，只保留当前用户输入
            # 这样确保AI分析的是当前用户的消息，而不是历史对话
            logger.info(f"跳过记忆载入，保持当前对话独立性")
            
            # 如果需要载入记忆，可以考虑以下逻辑：
            # 1. 只载入用户上下文信息（如兴趣偏好）
            # 2. 不载入历史对话消息到messages列表
            # 3. 将历史对话单独存储在state的其他字段中
            
        except Exception as e:
            logger.warning(f"载入记忆失败: {str(e)}")
        
        return state
    
    async def _classify_intent(self, state: AgentState) -> AgentState:
        print(f"测试点：意图分类")
        """分类用户意图"""
        user_message = state["messages"][-1].content
        print(f"测试点：当前消息列表长度: {len(state['messages'])}")
        print(f"测试点：用户消息内容: {user_message}")
        print(f"测试点：完整state结构: {state}")
        
        try:
            messages = [
                SystemMessage(content=self.CLASSIFY_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            classification = response.content.strip()
            print(f"测试点：AI分类结果: {classification}")
            
            # 验证分类结果
            valid_types = ["准确搜索", "含糊搜索", "兴趣调整", "其它"]
            if classification in valid_types:
                state["response_type"] = classification
                print(f"测试点：分类成功，设置response_type为: {classification}")
                logger.info(f"意图分类成功: {classification}")
            else:
                # 分类失败，默认为其它
                state["response_type"] = "其它"
                print(f"测试点：分类失败，默认设置为: 其它")
                logger.warning(f"意图分类无效: {classification}，默认为其它")
                
        except Exception as e:
            logger.error(f"意图分类失败: {str(e)}")
            state["response_type"] = "其它"
            print(f"测试点：分类异常，设置为: 其它")
        
        return state
    
    def _route_by_intent(self, state: AgentState) -> str:
        """根据意图路由"""
        route = state["response_type"]
        print(f"测试点：路由决策，response_type为: {route}")
        return route
    
    async def _extract_keywords(self, state: AgentState) -> AgentState:
        print(f"测试点：提取关键词")
        """提取关键词"""
        user_message = state["messages"][-1].content
        
        try:
            messages = [
                SystemMessage(content=self.EXTRACT_KEYWORDS_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            keywords_text = response.content.strip()
            print(f"测试点：提取的关键词: {keywords_text}")
            
            if keywords_text and keywords_text != "无":
                keywords = [kw.strip() for kw in keywords_text.split(',') if kw.strip()]
                state["extracted_keywords"] = keywords[:3]  # 最多3个
                logger.info(f"关键词提取成功: {keywords}")
            else:
                state["extracted_keywords"] = []
                logger.info("未提取到有效关键词")
                
        except Exception as e:
            logger.error(f"关键词提取失败: {str(e)}")
            state["extracted_keywords"] = []
        
        return state
    
    async def _search_precise(self, state: AgentState) -> AgentState:
        """准确搜索：提取关键词，添加兴趣，搜索入库"""
        try:
            keywords = state.get("extracted_keywords", [])
            
            if not keywords:
                # 没有关键词，返回提示
                state["messages"].append(AIMessage(content="抱歉，无法从您的请求中提取到有效的搜索关键词，请提供更具体的内容。"))
                return state
            
            # 1. 添加到用户兴趣
            await add_user_interests(state["user_id"], keywords)
            logger.info(f"已将关键词添加到用户兴趣: {keywords}")
            
            # 2. 搜索新闻并入库
            news_service = await get_news_service()
            request = NewsSearchRequest(
                session_id=state["session_id"],
                keywords=keywords,
                num_results=10,
                language="zh-cn",
                country="cn",
                time_period="1d"
            )
            
            result = await news_service.search_and_save_news(request)
            
            # 3. 格式化响应
            if result.status == "success":
                saved_count = getattr(result, 'saved_count', 0)
                total_found = getattr(result, 'total_found', 0)
                response = f"""✅ 搜索完成！

🔍 **搜索关键词**: {', '.join(keywords)}
📊 **搜索结果**: 找到 {total_found} 篇新闻，新增保存 {saved_count} 篇
🎯 **兴趣更新**: 已将这些关键词添加到您的兴趣偏好中

💡 下次可以直接说"今日新闻"，我会优先推荐相关内容！"""
            else:
                response = f"❌ 搜索失败: {getattr(result, 'message', '未知错误')}"
            
            state["messages"].append(AIMessage(content=response))
            state["search_result"] = {
                "success": result.status == "success",
                "keywords": keywords,
                "saved_count": getattr(result, 'saved_count', 0),
                "total_found": getattr(result, 'total_found', 0)
            }
            
        except Exception as e:
            logger.error(f"准确搜索失败: {str(e)}")
            state["messages"].append(AIMessage(content="搜索过程中出现错误，请稍后重试。"))
            
        return state
    
    async def _search_general(self, state: AgentState) -> AgentState:
        """含糊搜索：使用通用关键词搜索热门新闻"""
        try:
            # 使用通用热门关键词
            general_keywords = ["热点", "今日"]
            
            news_service = await get_news_service()
            request = NewsSearchRequest(
                session_id=state["session_id"],
                keywords=general_keywords,
                num_results=15,  # 多搜索一些
                language="zh-cn",
                country="cn",
                time_period="1d"
            )
            
            result = await news_service.search_and_save_news(request)
            
            # 格式化响应
            if result.status == "success":
                saved_count = getattr(result, 'saved_count', 0)
                total_found = getattr(result, 'total_found', 0)
                response = f"""📰 今日热门新闻为您更新！

� **搜索结果**: 找到 {total_found} 篇热门新闻，新增保存 {saved_count} 篇
� **内容范围**: 涵盖政治、经济、科技、体育等各领域热点
⚡ **实时更新**: 已为您入库最新资讯

💡 **提示**: 如果您对某个领域特别感兴趣，可以告诉我具体的关键词！"""
            else:
                response = f"❌ 获取热门新闻失败: {getattr(result, 'message', '未知错误')}"
            
            state["messages"].append(AIMessage(content=response))
            state["search_result"] = {
                "success": result.status == "success",
                "keywords": general_keywords,
                "saved_count": getattr(result, 'saved_count', 0),
                "total_found": getattr(result, 'total_found', 0)
            }
            
        except Exception as e:
            logger.error(f"含糊搜索失败: {str(e)}")
            state["messages"].append(AIMessage(content="获取热门新闻时出现错误，请稍后重试。"))
            
        return state
    
    async def _manage_interests(self, state: AgentState) -> AgentState:
        """处理兴趣调整"""
        user_message = state["messages"][-1].content
        
        try:
            # 使用AI分析兴趣调整意图
            messages = [
                SystemMessage(content=self.INTEREST_INTENT_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            intent_result = response.content.strip()
            
            if "|" not in intent_result or intent_result.startswith("无法确定"):
                state["messages"].append(AIMessage(content="抱歉，我无法理解您的兴趣调整需求，请更明确地表达。"))
                return state
            
            operation, keywords_str = intent_result.split("|", 1)
            operation = operation.strip()
            
            if operation == "查看":
                # 查看当前兴趣
                current_interests = await get_user_interests(state["user_id"])
                if current_interests:
                    interests_text = "、".join(current_interests)
                    response = f"📋 您当前的兴趣偏好：{interests_text}"
                else:
                    response = "📋 您还没有设置任何兴趣偏好。"
                    
            elif operation == "增加" and keywords_str != "无":
                # 添加兴趣
                keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
                if keywords:
                    success = await add_user_interests(state["user_id"], keywords)
                    if success:
                        response = f"✅ 已将「{', '.join(keywords)}」添加到您的兴趣中！"
                    else:
                        response = "❌ 添加兴趣失败，请稍后重试。"
                else:
                    response = "🤔 请明确告诉我您想添加哪些兴趣。"
                    
            elif operation == "删除" and keywords_str != "无":
                # 删除兴趣
                keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
                if keywords:
                    success = await remove_user_interests(state["user_id"], keywords)
                    if success:
                        response = f"✅ 已从您的兴趣中移除「{', '.join(keywords)}」！"
                    else:
                        response = "❌ 移除兴趣失败，请稍后重试。"
                else:
                    response = "🤔 请明确告诉我您想移除哪些兴趣。"
            else:
                response = "🤔 抱歉，我无法理解您的兴趣调整需求。"
                
        except Exception as e:
            logger.error(f"兴趣管理失败: {str(e)}")
            response = "❌ 兴趣管理功能暂时不可用，请稍后重试。"
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    async def _handle_other(self, state: AgentState) -> AgentState:
        """处理其他类型的请求 - 继续对话"""
        user_message = state["messages"][-1].content
        
        # 简单的对话回复
        greetings = ["你好", "您好", "hi", "hello"]
        questions = ["是什么", "怎么用", "如何", "能做什么"]
        
        if any(greeting in user_message.lower() for greeting in greetings):
            response = "您好！我是智能新闻助手，可以帮您搜索新闻、管理兴趣偏好。请告诉我您想了解什么新闻吧！"
        elif any(question in user_message for question in questions):
            response = """我是智能新闻助手，主要功能包括：

🔍 **新闻搜索** - 说出关键词，我帮您找新闻
📰 **热门资讯** - 获取今日热点新闻  
🎯 **兴趣管理** - 设置和调整您的新闻偏好

试试对我说"今天的科技新闻"或"我对体育感兴趣"吧！"""
        else:
            response = "抱歉，我主要专注于新闻搜索和兴趣管理。请告诉我您想了解什么新闻，或者需要调整兴趣偏好。"
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    async def _save_memory(self, state: AgentState) -> AgentState:
        """保存会话记忆"""
        try:
            print(f"测试点：开始保存记忆")
            # 获取当前记忆
            memory = self.memory_store.get_memory(state["session_id"]) or {
                "conversation_history": [],
                "user_context": {}
            }
            
            # 添加本轮对话 - 只保存用户输入和AI最终回复
            user_msg = None
            ai_msg = None
            
            # 找到最初的用户输入（第一条消息）
            for msg in state["messages"]:
                if isinstance(msg, HumanMessage):
                    user_msg = msg.content
                    break
            
            # 找到最后的AI回复
            for msg in reversed(state["messages"]):
                if isinstance(msg, AIMessage):
                    ai_msg = msg.content
                    break
            
            print(f"测试点：要保存的用户消息: {user_msg}")
            print(f"测试点：要保存的AI回复: {ai_msg}")
            
            if user_msg and ai_msg:
                memory["conversation_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "user": user_msg,
                    "assistant": ai_msg
                })
                
                # 限制历史记录长度
                if len(memory["conversation_history"]) > 10:
                    memory["conversation_history"] = memory["conversation_history"][-10:]
                
                print(f"测试点：保存对话成功，历史记录条数: {len(memory['conversation_history'])}")
            
            # 保存记忆
            self.memory_store.save_memory(state["session_id"], memory)
            
        except Exception as e:
            logger.warning(f"保存记忆失败: {str(e)}")
            print(f"测试点：保存记忆失败: {str(e)}")
        
        return state
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            test_msg = [HumanMessage(content="test")]
            await self.llm.ainvoke(test_msg)
            return True
        except:
            return False

# 全局服务实例
_news_agent_service: Optional[NewsAgentService] = None


async def get_news_agent_service() -> NewsAgentService:
    """获取智能新闻助手服务实例（单例模式）"""
    global _news_agent_service
    if _news_agent_service is None:
        _news_agent_service = NewsAgentService()
    return _news_agent_service


# 为 API 兼容性添加的简单方法
async def health_check() -> bool:
    """健康检查"""
    try:
        service = await get_news_agent_service()
        return await service.health_check()
    except:
        return False
    