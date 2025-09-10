import streamlit as st
from rag.doc_fetcher import export_drive_file
from rag.image_fetcher import pdf_image_pages_to_images
from rag.model_analyst import analyze_image_mock
from dto.pdf_image_dto import pdf_image_dto
from rag.model_vector import vector, query  # 你的流式query函数（返回生成器）


def extract_page_number(image_path: str) -> int:
    import re
    pattern = r'_page(\d+)\.'
    match = re.search(pattern, image_path)
    return int(match.group(1)) if match else None


def init_app():
    st.title("文档问答助手")

    if "chat_history" not in st.session_state:
        # 聊天历史格式：列表，每个元素是 (用户问题, 模型答案) 的元组
        st.session_state.chat_history = []

    # -------------------------- 2. 加载文档（缓存，避免重复解析） --------------------------
    @st.cache_resource
    def load_document(file_id):
        with st.spinner("正在加载文档..."):
            file_path = export_drive_file(file_id=file_id)
            image_paths = pdf_image_pages_to_images(file_path)

            image_dtos = []
            for img_path in image_paths:
                page_num = extract_page_number(img_path)
                image_dto = pdf_image_dto(file_id=file_id, page_number=page_num)
                image_dto.analysis_result = analyze_image_mock(img_path)
                image_dtos.append(image_dto)

            query_engine = vector(file_path=file_path, file_id=file_id, dtos=image_dtos)
            st.success("向量数据库构建完成，可以开始提问了")
            return query_engine

    # 固定文档ID（可根据需求改为用户输入）
    file_id = "1ZawDnCnk8q4lUVrDhxPgwcK-aW_una4nSV4_imiWsYA"
    query_engine = load_document(file_id)

    # -------------------------- 3. 展示历史聊天记录 --------------------------
    st.subheader("聊天记录")
    # 倒序展示（最新的在最下面），用Streamlit的容器组件包裹，区分用户/助手
    chat_container = st.container()
    with chat_container:
        for idx, (user_q, assistant_a) in enumerate(st.session_state.chat_history):
            # 用户问题样式（蓝色背景）
            st.markdown(f"""
                <div style="background-color:#e6f7ff; padding:10px; border-radius:8px; margin-bottom:8px;">
                    <strong>你:</strong> {user_q}
                </div>
            """, unsafe_allow_html=True)
            # 助手答案样式（灰色背景）
            st.markdown(f"""
                <div style="background-color:#f5f5f5; padding:10px; border-radius:8px; margin-bottom:16px;">
                    <strong>助手:</strong> {assistant_a}
                </div>
            """, unsafe_allow_html=True)

    # -------------------------- 4. 新问题输入与提交（流式输出+记录保存） --------------------------
    st.subheader("请输入新问题")
    user_question = st.text_input("问题", placeholder="例如：What is BMS?")

    # 按钮1：提交自定义问题
    if st.button("获取答案") and user_question:
        # 1. 先清空当前输入框（可选，提升体验）
        st.session_state.user_input = ""

        # 2. 流式生成答案并实时展示
        result_placeholder = st.empty()  # 占位符，用于动态更新流式内容
        full_answer = ""

        # 迭代流式query的生成器，获取每个片段
        for chunk in query(user_question, query_engine):
            full_answer += chunk
            # 实时更新当前答案（临时展示，后续会存入历史）
            result_placeholder.markdown(f"""
                <div style="background-color:#f5f5f5; padding:10px; border-radius:8px;">
                    <strong>助手（生成中）:</strong> {full_answer}
                </div>
            """, unsafe_allow_html=True)

        # 3. 流式结束：移除临时占位符，将问答存入历史记录
        result_placeholder.empty()
        st.session_state.chat_history.append((user_question, full_answer))
        # 刷新页面以展示最新历史（Streamlit特性：修改session_state后需触发重跑）
        st.rerun()

    # -------------------------- 5. 示例问题按钮（同样保留记录） --------------------------
    st.subheader("示例问题")
    example_questions = [
        "What is BMS?",
        "What is BMS problem now?",
        "How to fix BMS problem now?"
    ]

    for q in example_questions:
        if st.button(q):
            with st.spinner(f"正在查找「{q}」的答案..."):
                # 流式获取答案
                full_answer = ""
                for chunk in query(q, query_engine):
                    full_answer += chunk

                # 存入历史记录并刷新
                st.session_state.chat_history.append((q, full_answer))
                st.rerun()




if __name__ == "__main__":
    init_app()