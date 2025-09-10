import streamlit as st
from rag.doc_fetcher import export_drive_file
from rag.image_fetcher import pdf_image_pages_to_images
from rag.model_analyst import analyze_image_mock
from dto.pdf_image_dto import pdf_image_dto
from rag.model_vector import vector, query


def extract_page_number(image_path: str) -> int:
    import re
    pattern = r'_page(\d+)\.'
    match = re.search(pattern, image_path)
    if match:
        return int(match.group(1))
    else:
        return None


def init_app():
    st.title("文档问答助手")

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

    file_id = "1ZawDnCnk8q4lUVrDhxPgwcK-aW_una4nSV4_imiWsYA"
    query_engine = load_document(file_id)
    st.subheader("请输入你的问题")
    user_question = st.text_input("问题")

    if st.button("获取答案") and user_question:
        with st.spinner("正在查找答案..."):
            result = query(user_question, query_engine)
            st.subheader("答案:")
            st.write(result)

    st.subheader("示例问题:")
    example_questions = [
        "What is BMS?",
        "What is BMS problem now?",
        "How to fix BMS problem now?"
    ]

    # 示例问题按钮
    for q in example_questions:
        if st.button(q):
            with st.spinner("正在查找答案..."):
                result = query(q, query_engine)
                st.subheader("答案:")
                st.write(result)


if __name__ == "__main__":
    init_app()
