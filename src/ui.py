import streamlit as st
from main import start
from rag.model_vector import query

# 页面配置 - 放在所有Streamlit命令之前
st.set_page_config(
    page_title="文档问答助手",
    page_icon="📄",
    layout="wide"
)

def init_app():
    st.title("📄 文档问答助手")
    st.write("上传文档后即可进行问答交互，支持流式回答和来源显示")

    # 初始化会话状态
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    if "query_engine" not in st.session_state:
        st.session_state.query_engine = None

    # 加载文档函数 - 使用session_state而非cache_resource，更灵活
    def load_document():
        if st.session_state.query_engine is None:
            with st.spinner("正在加载文档并构建向量数据库..."):
                try:
                    st.session_state.query_engine = start()
                    st.success("✅ 向量数据库构建完成，可以开始提问了")
                except Exception as e:
                    st.error(f"❌ 加载文档失败: {str(e)}")
                    return None
        return st.session_state.query_engine

    # 加载文档按钮 - 让用户主动触发加载
    if st.button("加载文档", key="load_doc_btn"):
        load_document()

    # 确保查询引擎已加载
    if st.session_state.query_engine is None:
        st.info("请先点击上方'加载文档'按钮初始化系统")
        return

    # 显示聊天历史
    st.subheader("💬 聊天记录")
    chat_container = st.container()
    with chat_container:
        for user_q, assistant_a in st.session_state.chat_history:
            st.markdown(f"""
                <div style="background-color:#e6f7ff; padding:10px; border-radius:8px; margin-bottom:8px;">
                    <strong>你:</strong> {user_q}
                </div>
            """, unsafe_allow_html=True)
            st.markdown(f"""
                <div style="background-color:#f5f5f5; padding:10px; border-radius:8px; margin-bottom:16px;">
                    <strong>助手:</strong> {assistant_a}
                </div>
            """, unsafe_allow_html=True)

    # 新问题输入
    st.subheader("❓ 请输入新问题")
    user_question = st.text_input("问题", placeholder="例如：What is BMS?")

    if st.button("获取答案", key="get_answer_btn") and user_question:
        with st.spinner("正在生成答案..."):
            # 流式生成答案并实时展示
            result_placeholder = st.empty()
            full_answer = ""

            try:
                # 调用查询函数
                for chunk in query(user_question, st.session_state.query_engine):
                    full_answer += chunk
                    result_placeholder.markdown(f"""
                        <div style="background-color:#f5f5f5; padding:10px; border-radius:8px;">
                            <strong>助手（生成中）:</strong> {full_answer}
                        </div>
                    """, unsafe_allow_html=True)

                # 更新历史记录
                st.session_state.chat_history.append((user_question, full_answer))
                result_placeholder.empty()
                st.rerun()
            except Exception as e:
                st.error(f"生成答案时出错: {str(e)}")

    # 示例问题
    st.subheader("🔍 示例问题")
    example_questions = [
        "What is BMS?",
        "What is BMS problem now?",
        "How to fix BMS problem now?"
    ]

    cols = st.columns(len(example_questions))
    for i, q in enumerate(example_questions):
        with cols[i]:
            if st.button(q, key=f"example_{i}"):
                with st.spinner(f"正在查找「{q}」的答案..."):
                    try:
                        full_answer = ""
                        for chunk in query(q, st.session_state.query_engine):
                            full_answer += chunk
                        st.session_state.chat_history.append((q, full_answer))
                        st.rerun()
                    except Exception as e:
                        st.error(f"生成答案时出错: {str(e)}")

if __name__ == "__main__":
    init_app()
