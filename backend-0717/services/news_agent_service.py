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
from services.user_interest_service import add_user_interests, remove_user_interests, get_user_interests, clear_user_interests, query_related_interests
from models.news import NewsSearchRequest
from models.agent import AgentState

logger = logging.getLogger(__name__)


class NewsAgentService:
    """智能新闻助手 - 专注新闻搜索和兴趣管理"""
    
    # 分类系统提示词
    CLASSIFY_PROMPT = """
你是一名智能的新闻搜索助手，接下来用户会发送一个输入，你需要判断这个输入属于以下四类中的哪一类。你的任务是理解语义并准确分类，而不是简单地匹配句式或关键词。请注意用户输入可能含糊不清，你需要尽可能地做出合理判断。

请从以下四类中选出最合适的一类：

1. 准确搜索：
用户表达了清晰、具体的新闻需求，句子中包含了可用于检索的主题关键词，表示用户想要看关于某个具体话题的新闻。哪怕话语较随意，只要体现了某个**具体事件、领域、国家、话题、人物**等都应归为准确搜索。
示例包括：
- “今天有什么关于中美关系的新闻？”
- “我想看最近 AI 或芯片的新闻”
- “美国发生什么大事了？”
- “最近关于台风的报道多不多？”

2. 含糊搜索：
用户表达了想看新闻的意愿，但没有提及任何具体的关键词或话题，只是泛泛地想了解近期动态，无法提取出有用关键词。
示例包括：
- “最近有什么新闻？”
- “给我推荐点新闻”
- “最近热点有哪些？”

3. 兴趣调整：
用户表达了自己对新闻的偏好变更，明确表示**想看、不要看、修改或查看某类新闻兴趣**。这类请求通常用于**调整用户画像或订阅偏好**，而不是单次获取新闻。
请特别关注以下四类表达：
- 增：我对军事比较感兴趣 / 多推荐点娱乐新闻
- 删：科技类新闻不用推荐了
- 改：我不再喜欢财经新闻了，换点别的
- 查：我现在都对哪些话题感兴趣？

例如但不限于：
- “我现在对军事比较感兴趣”
- “科技类新闻先不用推荐了”
- “多推荐点娱乐新闻”
- “我想看看我对什么感兴趣”

4. 其它：
用户输入不是新闻请求，也不涉及偏好调整，而是闲聊、计算、订票、个人事务等其他行为。
示例包括：
- “你好，在吗？”
- “2+2=？”
- “我想订机票去北京”

---

请你根据用户输入内容，判断其最接近哪一类。**只输出下列四个词中的一个，不要包含任何解释或其他内容**：

准确搜索  
含糊搜索  
兴趣调整  
其它
"""
    
    # 关键词提取提示词
    EXTRACT_KEYWORDS_PROMPT = """
你是一个关键词提取助手，任务是从用户的输入中识别出与“新闻主题”相关的关键词。

# 要求：
1. **关键词必须是具体的主题内容**，如“AI”、“股市”、“欧冠”、“特斯拉”、“台风”等。
2. **不要返回模糊、无意义的词语**，如“新闻”、“事情”、“内容”等。
3. **除非极特殊情况，否则严禁返回“无法提取”。
4. **输出格式：关键词1,关键词2,...**（关键词用中文逗号或英文逗号分隔，全部保留中文即可）
5. **不要编造用户没提到的内容。**

# 示例：
输入：请搜索今日的股票行情。
输出：股票,行情

输入：告诉我AI领域最近的进展。
输出：AI

输入：我想知道今天世界杯的比赛结果。
输出：世界杯,比赛

输入：现在天气好糟糕，台风是不是要来了？
输出：台风

输入：能不能给我一些最新的军事新闻？
输出：军事

输入：你好。
输出：无法提取
"""

    
    # 兴趣调整提示词 - 智能两阶段SQL自动执行版本
    INTEREST_INTENT_PROMPT = """你是一名用户兴趣管理助手。用户的输入表达了对新闻兴趣的管理需求，你需要智能分析用户意图并生成相应的MongoDB操作指令。

用户当前的兴趣数据存储在MongoDB的users集合中，结构如下：
```
{
  "_id": "用户ID", 
  "news_preferences": {
    "news_interests": ["科技", "体育", "娱乐", "地铁", "高铁", "轨道交通", ...] // 用户当前兴趣列表
  }
}
```

你需要智能理解用户的复杂需求，支持**两阶段执行**：

**第一阶段：智能查询分析**
当用户提到模糊的删除需求时（如"删除和XX相关的"、"清理XX类的"），先查询用户现有兴趣，找出相关项目。

**第二阶段：精确执行操作**
基于查询结果，生成精确的操作指令。

**支持的操作类型：**
- `QUERY:` - 查询当前兴趣
- `QUERY_RELATED:关键词` - 查询与特定关键词相关的兴趣（用于智能分析）
- `ADD:关键词1,关键词2` - 添加兴趣
- `REMOVE:关键词1,关键词2` - 删除特定兴趣
- `CLEAR:` - 清空所有兴趣
- `REPLACE:删除关键词1,关键词2|添加关键词3,关键词4` - 替换兴趣
- `UNKNOWN:` - 无法理解用户意图

**智能分析规则：**
1. **模糊删除检测**：当用户说"删除和XX相关的"、"清理XX类的"、"不要XX方面的"时，先使用 QUERY_RELATED:XX 查询
2. **精确操作**：当用户明确指定兴趣名称时，直接执行操作
3. **两阶段处理**：复杂需求分解为查询+操作两个阶段
4. 关键词必须从用户输入中真实提取，不要臆造
5. 每个操作独占一行

**示例分析：**

**简单直接操作：**
用户输入："我对AI和机器学习感兴趣"
分析：用户明确指定要添加的兴趣
输出：ADD:AI,机器学习

用户输入："删除科技兴趣"
分析：用户明确指定要删除的兴趣
输出：REMOVE:科技

**智能两阶段操作：**
用户输入："把和轨道交通相关的兴趣全部删掉"
分析：用户要删除相关的兴趣，但不知道具体有哪些，需要先查询
输出：QUERY_RELATED:轨道交通

用户输入："清理所有体育类的兴趣"
分析：需要先找出所有体育相关的兴趣
输出：QUERY_RELATED:体育

用户输入："不要科技方面的兴趣了"
分析：需要先查询科技相关的兴趣
输出：QUERY_RELATED:科技

**复合操作：**
用户输入："删除所有科技相关的，然后添加娱乐"
分析：先查询科技相关的兴趣，然后删除，最后添加娱乐
输出：
QUERY_RELATED:科技
ADD:娱乐

用户输入："把体育换成音乐"
分析：明确的替换操作
输出：REPLACE:体育|音乐

**特殊操作：**
用户输入："把所有兴趣都删掉"
分析：清空所有兴趣
输出：CLEAR:

用户输入："我想看看我现在对什么感兴趣"
分析：查看当前兴趣
输出：QUERY:

现在请智能分析用户输入并生成操作："""



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
        """构建 LangGraph 工作流，手动管理记忆，入口为 classify_intent"""
        workflow = StateGraph(AgentState)

        # 添加节点
        workflow.add_node("classify_intent", self._classify_intent)
        workflow.add_node("extract_keywords", self._extract_keywords)
        workflow.add_node("search_precise", self._search_precise)
        workflow.add_node("search_general", self._search_general)
        workflow.add_node("manage_interests", self._manage_interests)
        workflow.add_node("handle_other", self._handle_other)
        workflow.add_node("save_memory", self._save_memory)  # 只保存用户输入问题

        # 入口点
        workflow.set_entry_point("classify_intent")

        # 分类后的条件路由
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

        # 含糊搜索流程
        workflow.add_edge("search_general", "save_memory")

        # 兴趣调整直接结束，不保存对话记忆
        workflow.add_edge("manage_interests", END)

        # 其它类型对话保存用户输入
        workflow.add_edge("handle_other", "save_memory")

        # 保存完毕后结束
        workflow.add_edge("save_memory", END)

        # 不使用 checkpointer，而是手动管理记忆
        return workflow.compile()
    
    async def process_user_message(self, user_id: str, session_id: str, message: str) -> Dict[str, Any]:
        """处理用户消息的主入口"""
        try:
            logger.info(f"处理用户消息 [用户: {user_id}, 会话: {session_id}]: {message}")

            # 加载历史记忆
            memory = self.memory_store.get_memory(session_id) or {
                "conversation_history": [],
                "user_context": {}
            }
            
            # 构建包含历史记忆的消息列表
            messages = []
            
            # 添加历史对话记录（最近5轮对话）
            recent_history = memory.get("conversation_history", [])[-5:]
            for history_item in recent_history:
                messages.append(HumanMessage(content=history_item["user"]))
                messages.append(AIMessage(content=history_item["assistant"]))
            
            # 添加当前用户消息
            messages.append(HumanMessage(content=message))
            
            print(f"测试点1：加载的历史消息数量: {len(messages)}")
            print(f"测试点2：历史记录条数: {len(recent_history)}")

            # 初始化状态
            initial_state = AgentState(
                messages=messages,  # 包含历史记忆的消息列表
                user_id=user_id,
                session_id=session_id,
                user_preferences=None,
                extracted_keywords=[],
                search_result=None,
                response_type="",
                interest_operation=None,
                interests_to_manage=[]
            )

            # 运行工作流，传入初始状态
            final_state = await self.graph.ainvoke(initial_state)

            # 提取智能体回复
            last_message = final_state["messages"][-1]
            response_content = getattr(last_message, 'content', str(last_message))

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
    
    async def _classify_intent(self, state: AgentState) -> AgentState:
        print(f"测试点3：意图分类")
        """分类用户意图"""
        user_message = state["messages"][-1].content
        print(f"测试点4：当前消息列表长度: {len(state['messages'])}")
        print(f"测试点5：用户消息内容: {user_message}")
        print(f"测试点6：完整state结构: {state}")
        
        try:
            # 构建包含上下文的提示消息
            messages = [
                SystemMessage(content=self.CLASSIFY_PROMPT),
                HumanMessage(content=user_message)
            ]
            print(f"测试点6.5：消息列表：{messages}")
            
            response = await self.llm.ainvoke(messages)
            classification = response.content.strip()
            print(f"测试点7：AI分类结果: {classification}")
            
            # 验证分类结果
            valid_types = ["准确搜索", "含糊搜索", "兴趣调整", "其它"]
            if classification in valid_types:
                state["response_type"] = classification
                print(f"测试点8：分类成功，设置response_type为: {classification}")
                logger.info(f"意图分类成功: {classification}")
            else:
                # 分类失败，默认为其它
                state["response_type"] = "其它"
                print(f"测试点9：分类失败，默认设置为: 其它")
                logger.warning(f"意图分类无效: {classification}，默认为其它")
                
        except Exception as e:
            logger.error(f"意图分类失败: {str(e)}")
            state["response_type"] = "其它"
            print(f"测试点10：分类异常，设置为: 其它")
        
        return state
    
    def _route_by_intent(self, state: AgentState) -> str:
        """根据意图路由"""
        route = state["response_type"]
        print(f"测试点11：路由决策，response_type为: {route}")
        return route
    
    async def _extract_keywords(self, state: AgentState) -> AgentState:
        print(f"测试点12：提取关键词")
        """提取关键词"""
        user_message = state["messages"][-1].content
        
        try:
            # 构建提示消息，只使用系统提示词和当前用户消息
            messages = [
                SystemMessage(content=self.EXTRACT_KEYWORDS_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            keywords_text = response.content.strip()
            print(f"测试点13：提取的关键词: {keywords_text}")
            
            if keywords_text and keywords_text not in ["无", "无法提取"]:
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
🎯 **兴趣更新**: 已将这些关键词添加到您的兴趣偏好中"""
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
                response = f"""📰 热门新闻为您更新！

📊 **搜索结果**: 找到 {total_found} 篇热门新闻，新增保存 {saved_count} 篇
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
        """处理兴趣调整 - 支持智能两阶段SQL自动执行"""
        user_message = state["messages"][-1].content
        
        try:
            # 使用AI分析兴趣调整意图
            messages = [
                SystemMessage(content=self.INTEREST_INTENT_PROMPT),
                HumanMessage(content=user_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            intent_result = response.content.strip()
            
            print(f"测试点20：兴趣管理AI响应: {intent_result}")
            
            # 解析AI响应，按行处理
            lines = [line.strip() for line in intent_result.split('\n') if line.strip()]
            operations_performed = []
            pending_operations = []  # 存储需要第二阶段执行的操作
            
            for line in lines:
                if line.startswith("UNKNOWN:"):
                    state["messages"].append(AIMessage(content="抱歉，我无法理解您的兴趣调整需求，请更明确地表达。"))
                    return state
                
                elif line.startswith("QUERY:"):
                    # 查看当前兴趣
                    current_interests = await get_user_interests(state["user_id"])
                    if current_interests:
                        interests_text = "、".join(current_interests)
                        operations_performed.append(f"📋 您当前的兴趣偏好：{interests_text}")
                    else:
                        operations_performed.append("📋 您还没有设置任何兴趣偏好。")
                
                elif line.startswith("QUERY_RELATED:"):
                    # 智能查询相关兴趣 - 第一阶段
                    keyword = line.replace("QUERY_RELATED:", "").strip()
                    if keyword:
                        related_interests = await query_related_interests(state["user_id"], keyword)
                        if related_interests:
                            operations_performed.append(f"🔍 找到与「{keyword}」相关的兴趣：{', '.join(related_interests)}")
                            # 自动生成第二阶段删除操作
                            pending_operations.append(f"REMOVE:{','.join(related_interests)}")
                        else:
                            operations_performed.append(f"🔍 未找到与「{keyword}」相关的兴趣")
                
                elif line.startswith("ADD:"):
                    keywords_str = line.replace("ADD:", "").strip()
                    if keywords_str:
                        keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
                        if keywords:
                            success = await add_user_interests(state["user_id"], keywords)
                            operations_performed.append(
                                f"✅ 已将「{', '.join(keywords)}」添加到您的兴趣中" if success 
                                else "❌ 添加兴趣失败，请稍后重试"
                            )
                
                elif line.startswith("REMOVE:"):
                    keywords_str = line.replace("REMOVE:", "").strip()
                    if keywords_str:
                        keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
                        if keywords:
                            success = await remove_user_interests(state["user_id"], keywords)
                            operations_performed.append(
                                f"✅ 已从您的兴趣中移除「{', '.join(keywords)}」" if success 
                                else "❌ 移除兴趣失败，请稍后重试"
                            )
                
                elif line.startswith("CLEAR:"):
                    # 清空所有兴趣
                    success = await clear_user_interests(state["user_id"])
                    operations_performed.append(
                        "✅ 已清空您的所有兴趣偏好" if success 
                        else "❌ 清空兴趣失败，请稍后重试"
                    )
                
                elif line.startswith("REPLACE:"):
                    # 替换兴趣
                    replace_content = line.replace("REPLACE:", "").strip()
                    
                    if "|" in replace_content:
                        parts = replace_content.split("|")
                        if len(parts) == 2:
                            remove_part = parts[0].strip()
                            add_part = parts[1].strip()
                            
                            # 处理删除操作
                            if remove_part:
                                remove_keywords = [kw.strip() for kw in remove_part.split(",") if kw.strip()]
                                if remove_keywords:
                                    success = await remove_user_interests(state["user_id"], remove_keywords)
                                    operations_performed.append(
                                        f"✅ 已从您的兴趣中移除「{', '.join(remove_keywords)}」" if success 
                                        else "❌ 移除兴趣失败"
                                    )
                            
                            # 处理增加操作
                            if add_part:
                                add_keywords = [kw.strip() for kw in add_part.split(",") if kw.strip()]
                                if add_keywords:
                                    success = await add_user_interests(state["user_id"], add_keywords)
                                    operations_performed.append(
                                        f"✅ 已将「{', '.join(add_keywords)}」添加到您的兴趣中" if success 
                                        else "❌ 添加兴趣失败"
                                    )
            
            # 执行第二阶段操作（如果有的话）
            for pending_op in pending_operations:
                if pending_op.startswith("REMOVE:"):
                    keywords_str = pending_op.replace("REMOVE:", "").strip()
                    if keywords_str:
                        keywords = [kw.strip() for kw in keywords_str.split(",") if kw.strip()]
                        if keywords:
                            success = await remove_user_interests(state["user_id"], keywords)
                            operations_performed.append(
                                f"✅ 已成功删除相关兴趣：「{', '.join(keywords)}」" if success 
                                else "❌ 删除相关兴趣失败，请稍后重试"
                            )
            
            # 检查是否有复合操作（如：删除A，添加B）
            user_message_lower = user_message.lower()
            if any(keyword in user_message_lower for keyword in ["替换成", "换成", "改成"]):
                # 智能解析替换操作
                replacement_keywords = self._extract_replacement_keywords(user_message)
                if replacement_keywords:
                    success = await add_user_interests(state["user_id"], replacement_keywords)
                    operations_performed.append(
                        f"✅ 已添加新的兴趣：「{', '.join(replacement_keywords)}」" if success 
                        else "❌ 添加新兴趣失败，请稍后重试"
                    )
            
            # 汇总回复
            if operations_performed:
                response = "\n".join(operations_performed)
            else:
                response = "🤔 抱歉，我无法理解您的兴趣调整需求。请尝试明确表达您想要增加、删除或查看哪些兴趣。"
                
        except Exception as e:
            logger.error(f"兴趣管理失败: {str(e)}")
            response = "❌ 兴趣管理功能暂时不可用，请稍后重试。"
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    def _extract_replacement_keywords(self, user_message: str) -> List[str]:
        """从用户消息中提取替换的新关键词"""
        try:
            # 简单的关键词提取逻辑
            replacement_indicators = ["替换成", "换成", "改成", "变成"]
            
            for indicator in replacement_indicators:
                if indicator in user_message:
                    # 找到指示词后的内容
                    parts = user_message.split(indicator)
                    if len(parts) > 1:
                        after_indicator = parts[1].strip()
                        # 简单的关键词提取（可以进一步优化）
                        # 移除常见的结尾词
                        cleanup_words = ["吧", "呗", "好吗", "行吗", "可以吗", "了", "啊", "哦"]
                        for word in cleanup_words:
                            after_indicator = after_indicator.replace(word, "")
                        
                        # 分割关键词
                        keywords = []
                        # 处理逗号分隔
                        if "," in after_indicator or "，" in after_indicator:
                            keywords = [kw.strip() for kw in after_indicator.replace("，", ",").split(",") if kw.strip()]
                        elif "和" in after_indicator:
                            keywords = [kw.strip() for kw in after_indicator.split("和") if kw.strip()]
                        else:
                            # 单个关键词
                            clean_keyword = after_indicator.strip()
                            if clean_keyword:
                                keywords = [clean_keyword]
                        
                        return keywords[:3]  # 最多3个关键词
            
            return []
            
        except Exception as e:
            logger.error(f"提取替换关键词失败: {str(e)}")
            return []
    
    async def _handle_other(self, state: AgentState) -> AgentState:
        """处理其他类型的请求 - 继续对话"""
        user_message = state["messages"][-1].content
        
        # 构建包含历史上下文的消息，用于自由对话
        messages = []
        
        # 添加系统提示词
        system_prompt = """你是一个智能新闻助手，主要功能是帮助用户搜索新闻和管理兴趣偏好。当用户不是询问新闻相关内容时，请友好地回应并引导用户使用你的新闻功能。"""
        messages.append(SystemMessage(content=system_prompt))
        
        # 添加历史对话上下文（最近3轮对话）
        if len(state["messages"]) > 1:
            context_messages = state["messages"][-7:-1]  # 排除最后一条用户消息
            for msg in context_messages:
                messages.append(msg)
        
        # 添加当前用户消息
        messages.append(HumanMessage(content=user_message))
        
        try:
            # 使用LLM生成回复
            llm_response = await self.llm.ainvoke(messages)
            response = llm_response.content.strip()
        except Exception as e:
            logger.error(f"LLM回复生成失败: {str(e)}")
            response = "抱歉，我主要专注于新闻搜索和兴趣管理。请告诉我您想了解什么新闻，或者需要调整兴趣偏好。"
        
        state["messages"].append(AIMessage(content=response))
        return state
    
    async def _save_memory(self, state: AgentState) -> AgentState:
        """保存会话记忆"""
        try:
            print(f"测试点14：开始保存记忆")
            # 获取当前记忆
            memory = self.memory_store.get_memory(state["session_id"]) or {
                "conversation_history": [],
                "user_context": {}
            }
            
            # 找到本轮对话的用户输入和AI回复
            # 由于消息列表包含历史记忆，我们需要找到最后一对用户-AI对话
            messages = state["messages"]
            
            # 从后往前找，找到最后一个AI消息和它对应的用户消息
            current_user_msg = None
            current_ai_msg = None
            
            # 找到最后的AI消息
            for i in range(len(messages) - 1, -1, -1):
                if isinstance(messages[i], AIMessage):
                    current_ai_msg = messages[i].content
                    break
            
            # 找到对应的用户消息（在AI消息之前的最后一个用户消息）
            if current_ai_msg:
                for i in range(len(messages) - 1, -1, -1):
                    if isinstance(messages[i], HumanMessage):
                        # 检查这是否是当前轮次的用户输入（不在历史记录中）
                        user_content = messages[i].content
                        # 如果这个用户消息不在历史记录中，说明是当前轮次的
                        is_in_history = any(
                            hist["user"] == user_content 
                            for hist in memory["conversation_history"]
                        )
                        if not is_in_history:
                            current_user_msg = user_content
                            break
            
            print(f"测试点15：要保存的用户消息: {current_user_msg}")
            print(f"测试点16：要保存的AI回复: {current_ai_msg}")
            
            if current_user_msg and current_ai_msg:
                memory["conversation_history"].append({
                    "timestamp": datetime.now().isoformat(),
                    "user": current_user_msg,
                    "assistant": current_ai_msg
                })
                
                # 限制历史记录长度（保留最近10轮对话）
                if len(memory["conversation_history"]) > 10:
                    memory["conversation_history"] = memory["conversation_history"][-10:]
                
                print(f"测试点17：保存对话成功，历史记录条数: {len(memory['conversation_history'])}")
                
                # 保存记忆
                self.memory_store.save_memory(state["session_id"], memory)
            else:
                print(f"测试点18：未找到有效的用户-AI对话对，跳过保存")
            
        except Exception as e:
            logger.warning(f"保存记忆失败: {str(e)}")
            print(f"测试点19：保存记忆失败: {str(e)}")
        
        return state

# 全局服务实例
_news_agent_service: Optional[NewsAgentService] = None


async def get_news_agent_service() -> NewsAgentService:
    """获取智能新闻助手服务实例（单例模式）"""
    global _news_agent_service
    if _news_agent_service is None:
        _news_agent_service = NewsAgentService()
    return _news_agent_service
    