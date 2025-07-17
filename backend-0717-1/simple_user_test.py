"""
简化版用户认证测试程序
只包含基本的注册、登录、会话管理功能
"""
import asyncio
import logging
from datetime import datetime

# 减少日志输出
logging.basicConfig(level=logging.ERROR)

# 导入服务
from user_api_compat import (
    create_user_account, 
    user_login, 
    create_user_session,
    get_user_sessions_list,
    delete_user_by_credentials,
    delete_user_session
)
from news_agent_compat import smart_search_news
from core.database import init_database, close_database


async def main():
    """简化版主程序"""
    print("🎯 用户认证系统 - 简化版")
    print("=" * 40)
    
    try:
        # 初始化数据库
        print("📡 连接数据库...")
        await init_database()
        print("✅ 数据库连接成功!")
        
        current_user = None
        
        while True:
            print("\n" + "=" * 30)
            if current_user is None:
                print("🔐 访客模式")
                print("1. 注册新用户")
                print("2. 用户登录")
                print("0. 退出")
            else:
                print(f"👤 用户: {current_user['username']}")
                print("1. 查看我的会话")
                print("2. 进入会话")
                print("3. 创建新会话")
                print("4. 删除指定会话")
                print("5. 删除我的账号")
                print("6. 退出登录")
                print("0. 退出程序")
            
            print("-" * 30)
            choice = input("请选择: ").strip()
            
            if choice == "0":
                break
            
            elif choice == "1":
                if current_user is None:
                    # 注册新用户
                    print("\n📝 注册新用户")
                    username = input("用户名: ").strip()
                    password = input("密码: ").strip()
                    
                    print("⏳ 创建中...")
                    result = await create_user_account(username, password)
                    
                    if result.user_id:  # 检查是否有有效的user_id
                        print(f"✅ 注册成功! 用户ID: {result.user_id}")
                    else:
                        print(f"❌ 注册失败: 用户名可能已存在或其他错误")
                
                else:
                    # 查看会话
                    print("\n📋 我的会话")
                    result = await get_user_sessions_list(current_user["user_id"])
                    
                    if result.get("status") == "success":
                        sessions = result["sessions"]
                        session_count = result.get("session_count", len(sessions))
                        
                        print(f"📊 会话统计: 共 {session_count} 个会话")
                        
                        if not sessions:
                            print("📭 暂无会话")
                        else:
                            print("\n� 会话列表:")
                            for i, session in enumerate(sessions, 1):
                                print(f"   {i}. {session['session_name']} (ID: {session['session_id'][:8]}...)")
                    else:
                        print(f"❌ 获取失败: {result.get('error', '未知错误')}")
            
            elif choice == "2":
                if current_user is None:
                    # 用户登录
                    print("\n🔐 用户登录")
                    username = input("用户名: ").strip()
                    password = input("密码: ").strip()
                    
                    print("⏳ 验证中...")
                    result = await user_login(username, password)
                    
                    if result.user_id:  # 检查是否有有效的user_id
                        current_user = {
                            "user_id": result.user_id,
                            "username": result.username
                        }
                        print(f"✅ 登录成功! 欢迎 {result.username}")
                        print(f"📊 找到 {len(result.sessions)} 个会话")
                    else:
                        print(f"❌ 登录失败: 用户名或密码错误")
                
                else:
                    # 进入会话
                    print("\n🚪 进入会话")
                    result = await get_user_sessions_list(current_user["user_id"])
                    
                    if result.get("status") == "success":
                        sessions = result["sessions"]
                        if not sessions:
                            print("📭 暂无会话，请先创建会话")
                        else:
                            print(f"📊 可用会话 ({len(sessions)} 个):")
                            for i, session in enumerate(sessions, 1):
                                print(f"   {i}. {session['session_name']} (ID: {session['session_id'][:8]}...)")
                            
                            try:
                                choice_num = int(input("\n请选择会话编号: ").strip())
                                if 1 <= choice_num <= len(sessions):
                                    selected_session = sessions[choice_num - 1]
                                    print(f"\n🎯 已选择会话: {selected_session['session_name']}")
                                    print(f"📧 会话ID: {selected_session['session_id']}")
                                    
                                    # 进入会话交互模式
                                    await session_interaction_mode(current_user, selected_session)
                                else:
                                    print("❌ 无效的会话编号")
                            except ValueError:
                                print("❌ 请输入有效的数字")
                    else:
                        print(f"❌ 获取会话失败: {result.get('error', '未知错误')}")
            
            elif choice == "3":
                if current_user is None:
                    print("❌ 无效选择")
                else:
                    # 创建会话
                    print("\n�💬 创建新会话")
                    session_name = input("会话名称 (可选): ").strip()
                    session_name = session_name if session_name else None
                    
                    print("⏳ 创建中...")
                    result = await create_user_session(current_user["user_id"], session_name)
                    
                    if result.session_id:  # 检查是否有有效的session_id
                        print(f"✅ 会话创建成功: {result.session_name}")
                    else:
                        print(f"❌ 创建失败: 用户不存在或其他错误")
            
            elif choice == "4":
                if current_user is None:
                    print("❌ 无效选择")
                else:
                    # 删除指定会话
                    print("\n🗑️ 删除会话")
                    result = await get_user_sessions_list(current_user["user_id"])
                    
                    if result.get("status") == "success":
                        sessions = result["sessions"]
                        if not sessions:
                            print("📭 暂无会话可删除")
                        else:
                            print(f"📊 可删除会话 ({len(sessions)} 个):")
                            for i, session in enumerate(sessions, 1):
                                print(f"   {i}. {session['session_name']} (ID: {session['session_id'][:8]}...)")
                            
                            try:
                                choice_num = int(input("\n请选择要删除的会话编号: ").strip())
                                if 1 <= choice_num <= len(sessions):
                                    selected_session = sessions[choice_num - 1]
                                    confirm = input(f"确认删除会话 '{selected_session['session_name']}' 吗? (输入 yes 确认): ").strip()
                                    
                                    if confirm.lower() == "yes":
                                        print("⏳ 删除中...")
                                        delete_result = await delete_user_session(selected_session['session_id'])
                                        
                                        if delete_result["status"] == "success":
                                            print(f"✅ 会话删除成功!")
                                            print(f"   {delete_result['message']}")
                                            if 'deleted_news' in delete_result:
                                                print(f"   级联删除了 {delete_result['deleted_news']} 条新闻")
                                        else:
                                            print(f"❌ 删除失败: {delete_result['message']}")
                                    else:
                                        print("❌ 取消删除")
                                else:
                                    print("❌ 无效的会话编号")
                            except ValueError:
                                print("❌ 请输入有效的数字")
                    else:
                        print(f"❌ 获取会话失败: {result.get('error', '未知错误')}")
            
            elif choice == "5" and current_user is not None:
                # 删除账号
                print("\n⚠️ 删除账号")
                print("警告: 删除账号将同时删除您的所有会话和相关新闻!")
                confirm = input("确认要删除账号吗? (输入 yes 确认): ").strip()
                
                if confirm.lower() == "yes":
                    password = input("请输入密码确认: ").strip()
                    print("⏳ 删除中...")
                    
                    result = await delete_user_by_credentials(current_user["username"], password)
                    
                    if result["status"] == "success":
                        print(f"✅ 账号删除成功!")
                        print(f"   {result['message']}")
                        print(f"   同时删除了 {result['deleted_sessions']} 个会话")
                        if 'deleted_news' in result:
                            print(f"   级联删除了 {result['deleted_news']} 条新闻")
                        current_user = None
                    else:
                        print(f"❌ 删除失败: {result['message']}")
                else:
                    print("❌ 取消删除")
            
            elif choice == "6" and current_user is not None:
                # 退出登录
                print(f"\n👋 {current_user['username']} 已退出登录")
                current_user = None
            
            else:
                print("❌ 无效选择")
    
    except KeyboardInterrupt:
        print("\n\n👋 用户退出")
    except Exception as e:
        print(f"\n❌ 程序错误: {str(e)}")
    finally:
        await close_database()
        print("📡 数据库连接已关闭")


async def test_cascade_deletion():
    """
    测试级联删除功能
    测试删除用户和会话时是否正确级联删除相关新闻
    """
    print("\n" + "="*50)
    print("🧪 级联删除功能测试")
    print("="*50)
    
    try:
        # 初始化数据库
        await init_database()
        
        # 1. 创建测试用户
        print("\n📝 1. 创建测试用户...")
        test_username = f"test_user_{int(datetime.now().timestamp())}"
        user_result = await create_user_account(test_username, "test123")
        
        if not user_result.user_id:
            print(f"❌ 创建用户失败: 用户名可能已存在")
            return
        
        print(f"✅ 测试用户创建成功: {test_username}")
        user_id = user_result.user_id
        
        # 2. 创建测试会话
        print("\n💬 2. 创建测试会话...")
        session1_result = await create_user_session(user_id, "测试会话1")
        session2_result = await create_user_session(user_id, "测试会话2")
        
        if not session1_result.session_id or not session2_result.session_id:
            print("❌ 创建会话失败")
            return
        
        print(f"✅ 创建了2个测试会话")
        session1_id = session1_result.session_id
        session2_id = session2_result.session_id
        
        # 3. 模拟添加新闻数据
        print("\n📰 3. 添加测试新闻...")
        from core.database import get_mongodb_database, Collections
        
        db = await get_mongodb_database()
        news_collection = db[Collections.NEWS]
        
        # 为每个会话添加测试新闻
        test_news = [
            {
                "_id": "test_news_1_session1",
                "session_id": session1_id,
                "title": "测试新闻1 - 会话1",
                "date": "2025-07-15",
                "keywords": ["测试"],
                "url": "http://test1.com",
                "source": "测试源1",
                "content": "测试内容1",
                "is_embedded": False
            },
            {
                "_id": "test_news_2_session1", 
                "session_id": session1_id,
                "title": "测试新闻2 - 会话1",
                "date": "2025-07-15",
                "keywords": ["测试"],
                "url": "http://test2.com",
                "source": "测试源2",
                "content": "测试内容2",
                "is_embedded": False
            },
            {
                "_id": "test_news_1_session2",
                "session_id": session2_id,
                "title": "测试新闻1 - 会话2",
                "date": "2025-07-15",
                "keywords": ["测试"],
                "url": "http://test3.com",
                "source": "测试源3",
                "content": "测试内容3",
                "is_embedded": False
            }
        ]
        
        await news_collection.insert_many(test_news)
        print(f"✅ 添加了 {len(test_news)} 条测试新闻")
        
        # 4. 验证数据
        print("\n📊 4. 验证数据...")
        news_count_session1 = await news_collection.count_documents({"session_id": session1_id})
        news_count_session2 = await news_collection.count_documents({"session_id": session2_id})
        print(f"   会话1新闻数: {news_count_session1}")
        print(f"   会话2新闻数: {news_count_session2}")
        
        # 5. 测试删除单个会话
        print("\n🗑️ 5. 测试删除单个会话...")
        delete_session_result = await delete_user_session(session1_id)
        print(f"   删除结果: {delete_session_result}")
        
        # 验证会话1的新闻被删除
        remaining_news_session1 = await news_collection.count_documents({"session_id": session1_id})
        remaining_news_session2 = await news_collection.count_documents({"session_id": session2_id})
        print(f"   删除后会话1新闻数: {remaining_news_session1}")
        print(f"   删除后会话2新闻数: {remaining_news_session2}")
        
        if remaining_news_session1 == 0 and remaining_news_session2 > 0:
            print("✅ 会话级联删除测试通过")
        else:
            print("❌ 会话级联删除测试失败")
        
        # 6. 测试删除用户
        print("\n🗑️ 6. 测试删除用户...")
        delete_user_result = await delete_user_by_credentials(test_username, "test123")
        print(f"   删除结果: {delete_user_result}")
        
        # 验证所有新闻被删除
        remaining_news_total = await news_collection.count_documents({
            "session_id": {"$in": [session1_id, session2_id]}
        })
        print(f"   删除后总新闻数: {remaining_news_total}")
        
        if remaining_news_total == 0:
            print("✅ 用户级联删除测试通过")
        else:
            print("❌ 用户级联删除测试失败")
        
        print("\n🎉 级联删除功能测试完成!")
        
    except Exception as e:
        print(f"❌ 测试过程出错: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        await close_database()


async def session_interaction_mode(current_user, selected_session):
    """
    会话交互模式 - 在此模式下用户可以搜索新闻和查看新闻概要
    
    Args:
        current_user: 当前用户信息
        selected_session: 选中的会话信息
    """
    session_id = selected_session['session_id']
    session_name = selected_session['session_name']
    
    print(f"\n{'='*50}")
    print(f"🎯 进入会话: {session_name}")
    print(f"📧 会话ID: {session_id}")
    print(f"👤 用户: {current_user['username']}")
    print(f"{'='*50}")
    
    while True:
        print(f"\n📰 新闻管理 - 会话: {session_name}")
        print("-" * 30)
        print("1. 智能体对话搜索")
        print("2. 查看新闻概要")
        print("3. 查看详细新闻列表")
        print("4. 返回主菜单")
        print("-" * 30)
        
        choice = input("请选择操作: ").strip()
        
        if choice == "1":
            # 智能体对话搜索
            await agent_conversation_mode(current_user, session_id)
            
        elif choice == "2":
            # 查看新闻概要
            await show_news_summary(session_id)
            
        elif choice == "3":
            # 查看详细新闻列表
            await show_detailed_news_list(session_id)
            
        elif choice == "4":
            print(f"👋 退出会话: {session_name}")
            break
            
        else:
            print("❌ 无效选择，请重新输入")


async def agent_conversation_mode(current_user, session_id):
    """
    智能体对话模式 - 自然语言交互搜索新闻
    
    Args:
        current_user: 当前用户信息
        session_id: 会话ID
    """
    print("\n🤖 智能体对话模式")
    print("=" * 30)
    print("💡 您可以用自然语言与我对话，例如：")
    print("   • '今天有什么重要新闻'")
    print("   • '人工智能和教育相关的最新报道'") 
    print("   • '科技公司最近怎么样了'")
    print("   • '给我推荐一些新闻'")
    print("=" * 30)
    
    # 导入智能体服务
    try:
        from services.news_agent_service import get_news_agent_service
    except ImportError as e:
        print(f"❌ 智能体服务不可用: {str(e)}")
        print("💡 可能的解决方案：")
        print("   1. 检查环境变量：DASHSCOPE_API_KEY 是否已设置")
        print("   2. 确认服务配置是否正确")
        print("   3. 检查 LangGraph 版本兼容性")
        input("按任意键返回...")
        return
    except Exception as e:
        print(f"❌ 智能体服务初始化失败: {str(e)}")
        print("💡 建议联系技术支持或检查日志文件")
        input("按任意键返回...")
        return
    
    # 测试智能体服务连接
    try:
        print("🔍 检查智能体服务状态...")
        agent_service = await get_news_agent_service()
        print("✅ 智能体服务可用")
    except Exception as e:
        print(f"❌ 智能体服务连接失败: {str(e)}")
        print("💡 可能的问题：")
        print("   - DASHSCOPE_API_KEY 未设置或无效")
        print("   - 网络连接问题")
        print("   - 服务配置错误")
        print("   - 运行诊断脚本：python diagnose_agent.py")
        input("按任意键返回...")
        return
    
    while True:
        print(f"\n💬 智能助手 (输入 '退出' 结束对话)")
        user_input = input("👤 您: ").strip()
        
        if not user_input:
            print("⚠️ 请输入您的问题或需求")
            continue
            
        if user_input.lower() in ['退出', 'exit', 'quit', 'q']:
            print("👋 结束对话，返回上级菜单")
            break
        
        print("🤖 助手正在思考...")
        
        try:
            # 调用智能体服务
            agent_service = await get_news_agent_service()
            response = await agent_service.process_user_message(
                user_id=current_user["user_id"],
                session_id=session_id,
                message=user_input
            )
            
            # 显示智能体回复
            print(f"\n🤖 助手: ")
            
            # 如果是HTML格式，简化显示
            reply_content = response.get("reply", "抱歉，我遇到了一些问题。")
            if reply_content.startswith('<'):
                # 简单解析HTML内容用于控制台显示
                import re
                # 移除HTML标签，保留文本
                clean_text = re.sub(r'<[^>]+>', '', reply_content)
                # 移除多余空行
                clean_text = re.sub(r'\n\s*\n', '\n', clean_text).strip()
                print(clean_text)
            else:
                print(reply_content)
            
            # 显示额外信息
            response_type = response.get("type", "")
            keywords_used = response.get("keywords_used", [])
            search_result = response.get("search_result", {})
            
            if response_type in ["news_general", "news_specific"] and search_result:
                print(f"\n📊 处理结果:")
                print(f"   🏷️ 类型: {response_type}")
                if keywords_used:
                    print(f"   � 关键词: {', '.join(keywords_used)}")
                if search_result.get("success"):
                    print(f"   ✅ 搜索成功")
                else:
                    print(f"   ❌ 搜索失败: {search_result.get('error', '未知错误')}")
                    
        except Exception as e:
            print(f"❌ 智能体服务异常: {str(e)}")
            print("💡 建议：请稍后重试或联系技术支持")


async def show_news_summary(session_id):
    """
    显示新闻概要
    
    Args:
        session_id: 会话ID
    """
    print("\n📊 新闻概要")
    print("-" * 20)
    
    try:
        # 导入统计函数
        from services.news_service import NewsService
        
        # 获取统计信息
        news_service = NewsService()
        stats = await news_service.get_session_news_statistics(session_id)
        
        # 包装为统一格式
        stats_result = {
            "status": "success",
            **stats
        }
        
        if stats_result.get("status") == "success":
            print(f"✅ 统计信息获取成功")
            print(f"   📰 总新闻数: {stats_result['total_count']}")
            print(f"   📅 今日新闻: {stats_result['today_count']}")
            print(f"   📆 最新日期: {stats_result.get('latest_date', '无')}")
            
            # 显示热门关键词
            top_keywords = stats_result.get('top_keywords', [])
            if top_keywords:
                print(f"   🔥 热门关键词 (前{len(top_keywords)}个):")
                for i, keyword_info in enumerate(top_keywords, 1):
                    print(f"      {i}. {keyword_info['keyword']} ({keyword_info['count']} 次)")
            else:
                print("   🔥 暂无关键词统计")
                
        else:
            error_msg = stats_result.get("error", "未知错误")
            print(f"❌ 获取统计失败: {error_msg}")
            
    except Exception as e:
        print(f"❌ 显示概要出错: {str(e)}")


async def show_detailed_news_list(session_id):
    """
    显示详细新闻列表
    
    Args:
        session_id: 会话ID
    """
    print("\n📋 详细新闻列表")
    print("-" * 25)
    
    try:
        # 获取显示参数
        try:
            limit = input("显示数量 (默认20): ").strip()
            limit = int(limit) if limit else 20
            limit = max(limit, 1)  # 至少显示1条
        except ValueError:
            limit = 20
            print("⚠️ 使用默认显示数量: 20")
        
        # 导入新闻列表函数
        from services.news_service import NewsService
        
        # 获取新闻列表
        news_service = NewsService()
        result = await news_service.get_session_news_list(
            session_id=session_id,
            limit=limit
        )
        
        if result.get("status") == "success":
            news_list = result["news_list"]
            total_count = result["total_count"]
            
            print(f"✅ 新闻列表获取成功")
            print(f"   📊 总数: {total_count}, 显示: {len(news_list)}")
            
            if not news_list:
                print("   📭 暂无新闻")
            else:
                print(f"\n{'='*60}")
                for i, news in enumerate(news_list, 1):
                    print(f"📰 {i}. {news['title']}")
                    print(f"   📅 日期: {news['date']}")
                    print(f"   📡 来源: {news['source']}")
                    print(f"   🔗 链接: {news['url']}")
                    print(f"   🏷️ 关键词: {', '.join(news['keywords'])}")
                    if news.get('category'):
                        print(f"   📂 分类: {news['category']}")
                    if news.get('sentiment'):
                        print(f"   😊 情感: {news['sentiment']}")
                    print(f"   🔍 已嵌入: {'是' if news.get('is_embedded') else '否'}")
                    print(f"   🆔 ID: {news['id']}")
                    print("-" * 60)
                    
        else:
            error_msg = result.get("error", "未知错误")
            print(f"❌ 获取新闻列表失败: {error_msg}")
            
    except Exception as e:
        print(f"❌ 显示新闻列表出错: {str(e)}")


# 如果直接运行此文件并带有 --test 参数，则运行测试
if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        print("运行级联删除功能测试...")
        asyncio.run(test_cascade_deletion())
    else:
        asyncio.run(main())
