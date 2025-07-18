"""
基于网络 API 的用户认证测试程序 - 美化版
通过 HTTP 请求实现用户注册、登录、会话管理等功能
"""
import asyncio
import httpx
import time
from typing import Optional, Dict, Any

BASE_URL = "http://127.0.0.1:8000/api/v1/users"  # API 服务的基础 URL

# 美化相关的工具函数
def print_banner():
    """打印程序横幅"""
    print("\n" + "🌟" * 50)
    print("🎯 用户认证系统 - 基于 API")
    print("   智能体对话 • 会话管理 • 用户认证")
    print("🌟" * 50)

def print_divider(char="─", length=50):
    """打印分隔线"""
    print(char * length)

def print_section_header(title: str, icon: str = "📋"):
    """打印章节标题"""
    print(f"\n{icon} {title}")
    print_divider()

def print_loading(message: str = "处理中", duration: float = 1.0):
    """显示加载动画"""
    print(f"⏳ {message}", end="", flush=True)
    for i in range(3):
        time.sleep(duration / 3)
        print(".", end="", flush=True)
    print(" 完成!")

def print_success(message: str):
    """打印成功消息"""
    print(f"✅ {message}")

def print_error(message: str):
    """打印错误消息"""
    print(f"❌ {message}")

def print_info(message: str):
    """打印信息消息"""
    print(f"💡 {message}")

def print_warning(message: str):
    """打印警告消息"""
    print(f"⚠️ {message}")

def get_styled_input(prompt: str, icon: str = "🔸") -> str:
    """获取用户输入，带样式"""
    return input(f"{icon} {prompt}: ").strip()

def print_menu_option(number: str, text: str, icon: str = "🔹"):
    """打印菜单选项"""
    print(f"  {icon} {number}. {text}")

def print_status_box(title: str, content: str, status: str = "info"):
    """打印状态框"""
    icons = {"info": "📊", "success": "✅", "error": "❌", "warning": "⚠️"}
    icon = icons.get(status, "📊")
    
    print(f"\n┌─ {icon} {title}")
    for line in content.split('\n'):
        print(f"│ {line}")
    print("└" + "─" * (len(title) + 3))

# 保持原有的 API 函数不变
async def register_user(username: str, password: str):
    """通过 API 注册用户"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/register", json={"username": username, "password": password})
        return response.json()

async def login_user(username: str, password: str):
    """通过 API 登录用户"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/auth/login", json={"username": username, "password": password})
        return response.json()

async def create_session(user_id: str, session_name: str = None):
    """通过 API 创建会话"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/sessions/create", json={"user_id": user_id, "session_name": session_name})
        return response.json()

async def delete_session(session_id: str):
    """通过 API 删除会话"""
    async with httpx.AsyncClient() as client:
        response = await client.delete(f"{BASE_URL}/sessions/{session_id}")
        return response.json()

async def delete_user(username: str, password: str):
    """通过 API 删除用户"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{BASE_URL}/profile/delete-account", json={"username": username, "password": password})
        return response.json()

async def get_user_sessions(user_id: str):
    """通过 API 获取用户的会话列表"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{BASE_URL}/sessions/list/{user_id}")
        return response.json()

async def select_ai_model():
    """选择 AI 模型"""
    print_section_header("选择AI模型", "🤖")
    
    models = [
        {"name": "模型 A", "desc": "高性能通用模型"},
        {"name": "模型 B", "desc": "快速响应模型"},
        {"name": "模型 C", "desc": "专业对话模型"}
    ]
    
    print("📋 可用的模型:")
    for i, model in enumerate(models, 1):
        print(f"  🔹 {i}. {model['name']} - {model['desc']}")
    print("  🔸 0. 返回上级菜单")
    
    print()
    while True:
        choice = get_styled_input("请选择模型编号", "🎯")
        
        if choice == "1":
            model_name = "模型 A"
            break
        elif choice == "2":
            model_name = "模型 B"
            break
        elif choice == "3":
            model_name = "模型 C"
            break
        elif choice == "0":
            return None
        else:
            print_error("无效的选择，请重试!")
            continue

    print_success(f"已选择 {model_name}")
    return model_name

async def agent_conversation_mode(current_user, session_id):
    """智能体对话模式 - 自然语言交互搜索新闻"""
    print_section_header("智能体对话模式", "🤖")
    
    # 显示使用提示
    print_status_box("使用提示", 
        "您可以用自然语言与我对话，例如：\n"
        "• '今天有什么重要新闻'\n"
        "• '人工智能和教育相关的最新报道'\n"
        "• '科技公司最近怎么样了'\n"
        "• '给我推荐一些新闻'", 
        "info")

    # 动态获取模型列表
    try:
        print_loading("正在获取模型列表")
        async with httpx.AsyncClient() as client:
            url = "http://127.0.0.1:8000/api/v1/chat/models"
            response = await client.get(url)

            if response.status_code == 200:
                models_data = response.json()
                available_models = models_data.get("data", {}).get("available_models", [])
                default_model = models_data.get("data", {}).get("default_model", "qwen-turbo")
                print_success("模型列表获取成功")
            else:
                print_warning(f"获取模型列表失败，使用默认配置 (状态码: {response.status_code})")
                available_models = ["qwen-turbo", "qwen-plus", "qwen-max"]
                default_model = "qwen-turbo"
    except Exception as e:
        print_error(f"获取模型列表出错: {str(e)}")
        available_models = ["qwen-turbo", "qwen-plus", "qwen-max"]
        default_model = "qwen-turbo"

    # 模型选择界面
    print_section_header("AI模型选择", "🎯")
    print("📋 可用模型:")
    for i, model in enumerate(available_models, 1):
        marker = " (默认)" if model == default_model else ""
        print(f"  🔹 {i}. {model}{marker}")

    print_info(f"提示: 直接回车使用默认模型 ({default_model})")
    choice = get_styled_input("请选择模型编号", "🤖")

    if not choice:
        selected_model = default_model
        print_success(f"使用默认模型: {default_model}")
    else:
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(available_models):
                selected_model = available_models[choice_num - 1]
                print_success(f"已选择模型: {selected_model}")
            else:
                selected_model = default_model
                print_warning(f"无效选择，使用默认模型: {default_model}")
        except ValueError:
            selected_model = default_model
            print_warning(f"输入无效，使用默认模型: {default_model}")

    # 对话循环
    print_section_header("开始对话", "💬")
    print_info("输入 '退出' 可返回主菜单")
    
    while True:
        print()
        user_input = get_styled_input("请输入您的问题", "🗨️")
        
        if user_input.lower() == "退出":
            print_success("退出智能体对话模式")
            break

        print_loading("助手正在思考", 2.0)
        
        try:
            timeout = httpx.Timeout(timeout=120.0, connect=10.0)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post("http://127.0.0.1:8000/api/v1/chat/chat", json={
                    "user_id": current_user["user_id"],
                    "session_id": session_id,
                    "message": user_input,
                    "model_name": selected_model
                })
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        reply = result.get("data", {}).get("reply", "无回复")
                        
                        # 格式化显示回复
                        print_status_box("助手回复", reply, "success")
                        
                        # 显示额外信息
                        data = result.get("data", {})
                        extra_info = []
                        if data.get("keywords_used"):
                            extra_info.append(f"🔍 关键词: {', '.join(data['keywords_used'])}")
                        if data.get("search_result"):
                            sr = data["search_result"]
                            if isinstance(sr, dict) and sr.get("success"):
                                extra_info.append(f"📊 搜索结果: 找到 {sr.get('total_found', 0)} 篇，保存 {sr.get('saved_count', 0)} 篇")
                        
                        if extra_info:
                            print_status_box("附加信息", "\n".join(extra_info), "info")
                    else:
                        print_error(f"智能体响应失败: {result.get('error', '未知错误')}")
                else:
                    print_error(f"智能体服务出错，状态码: {response.status_code}")
                    
        except httpx.TimeoutException:
            print_error("请求超时")
            print_info("智能体处理可能需要较长时间，请稍后重试")
        except httpx.ConnectError:
            print_error("连接失败")
            print_info("请确保API服务正在运行 (python main.py)")
        except Exception as e:
            print_error(f"未知错误: {str(e)}")

def show_guest_menu():
    """显示访客菜单"""
    print_section_header("访客模式", "🔐")
    print_menu_option("1", "注册新用户", "👤")
    print_menu_option("2", "用户登录", "🔑")
    print_menu_option("0", "退出", "👋")

def show_user_menu(username: str):
    """显示用户菜单"""
    print_section_header(f"用户: {username}", "👤")
    print_menu_option("1", "查看我的会话", "📋")
    print_menu_option("2", "创建新会话", "➕")
    print_menu_option("3", "删除会话", "🗑️")
    print_menu_option("4", "删除账号", "❌")
    print_menu_option("5", "智能体对话模式", "🤖")
    print_menu_option("0", "退出登录", "🚪")

def display_sessions(sessions: list):
    """显示会话列表"""
    if not sessions:
        print_info("暂无会话")
        return False
    
    print_section_header("会话列表", "📋")
    for i, session in enumerate(sessions, 1):
        print(f"  🔹 {i}. {session['session_name']} (ID: {session['session_id']})")
    return True

async def main():
    """基于网络 API 的主程序"""
    print_banner()
    
    current_user = None

    while True:
        print()
        print_divider("═")
        
        if current_user is None:
            show_guest_menu()
        else:
            show_user_menu(current_user['username'])

        print()
        choice = get_styled_input("请选择操作", "🎯")

        if choice == "1":
            if current_user is None:
                # 注册新用户
                print_section_header("用户注册", "👤")
                username = get_styled_input("请输入用户名", "👤")
                password = get_styled_input("请输入密码", "🔒")
                
                print_loading("正在注册")
                result = await register_user(username, password)
                
                if result.get("status") == "success":
                    print_success("注册成功!")
                else:
                    print_error(f"注册失败: {result}")
            else:
                # 查看会话
                print_loading("正在获取会话列表")
                result = await get_user_sessions(current_user["user_id"])
                display_sessions(result.get("sessions", []))
                
        elif choice == "2":
            if current_user is None:
                # 用户登录
                print_section_header("用户登录", "🔑")
                username = get_styled_input("请输入用户名", "👤")
                password = get_styled_input("请输入密码", "🔒")
                
                print_loading("正在登录")
                result = await login_user(username, password)
                
                if "user_id" in result:
                    current_user = {"user_id": result["user_id"], "username": username}
                    print_success(f"登录成功! 欢迎回来, {username}!")
                else:
                    print_error(f"登录失败: {result}")
            else:
                # 创建新会话
                print_section_header("创建新会话", "➕")
                session_name = get_styled_input("请输入会话名称 (可选)", "📝")
                
                print_loading("正在创建会话")
                result = await create_session(current_user["user_id"], session_name or None)
                
                if result.get("status") == "success":
                    print_success("会话创建成功!")
                else:
                    print_error(f"创建失败: {result}")
                    
        elif choice == "3" and current_user is not None:
            # 删除会话
            result = await get_user_sessions(current_user["user_id"])
            sessions = result.get("sessions", [])
            
            if display_sessions(sessions):
                print()
                try:
                    choice_num = int(get_styled_input("请输入要删除的会话编号", "🗑️"))
                    if 1 <= choice_num <= len(sessions):
                        session_id = sessions[choice_num - 1]["session_id"]
                        session_name = sessions[choice_num - 1]["session_name"]
                        
                        confirm = get_styled_input(f"确认删除会话 '{session_name}'? (yes/no)", "⚠️")
                        if confirm.lower() == "yes":
                            print_loading("正在删除会话")
                            delete_result = await delete_session(session_id)
                            
                            if delete_result.get("status") == "success":
                                print_success("会话删除成功!")
                            else:
                                print_error(f"删除失败: {delete_result}")
                        else:
                            print_info("取消删除")
                    else:
                        print_error("无效的会话编号")
                except ValueError:
                    print_error("请输入有效的数字")
                    
        elif choice == "4" and current_user is not None:
            # 删除账号
            print_section_header("删除账号", "❌")
            print_warning("此操作不可逆，请谨慎操作!")
            
            confirm = get_styled_input("确认删除账号吗? (yes/no)", "⚠️")
            if confirm.lower() == "yes":
                password = get_styled_input("请输入密码确认", "🔒")
                
                print_loading("正在删除账号")
                result = await delete_user(current_user["username"], password)
                
                if result.get("status") == "success":
                    print_success("账号删除成功!")
                    current_user = None
                else:
                    print_error(f"删除失败: {result}")
            else:
                print_info("取消删除")
                
        elif choice == "5" and current_user is not None:
            # 智能体对话模式
            result = await get_user_sessions(current_user["user_id"])
            sessions = result.get("sessions", [])
            
            if display_sessions(sessions):
                print()
                try:
                    choice_num = int(get_styled_input("请选择会话编号进入智能体对话模式", "🤖"))
                    if 1 <= choice_num <= len(sessions):
                        session_id = sessions[choice_num - 1]["session_id"]
                        await agent_conversation_mode(current_user, session_id)
                    else:
                        print_error("无效的会话编号")
                except ValueError:
                    print_error("请输入有效的数字")
                    
        elif choice == "0":
            if current_user is None:
                print_success("感谢使用，再见!")
                break
            else:
                print_success("已退出登录!")
                current_user = None
        else:
            print_error("无效的选择，请重试!")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n👋 程序已终止，再见!")
    except Exception as e:
        print(f"\n❌ 程序出现错误: {str(e)}")