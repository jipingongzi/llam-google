import os
import shutil
from uuid import uuid1
from typing import List
from llama_index.core import SimpleDirectoryReader, Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.indices.base import BaseQueryEngine
from dto.pdf_image_dto import pdf_image_dto
from llama_index.core import Settings
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# 初始化全局LLM和嵌入模型
llm = DeepSeek(model="deepseek-chat", api_key="sk-9b5776bd68e045f7ae2171077134b2a4")
Settings.llm = llm
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


def vector(file_id: str, file_path: str, dtos: List[pdf_image_dto]) -> BaseQueryEngine:
    pdf_documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    dto_documents = []
    for dto in dtos:
        if dto.analysis_result and dto.analysis_result.strip():
            metadata = {
                "file_id": file_id,
                "page_number": dto.page_number,
                "source_type": "pdf_image",
                "pdf_source_path": file_path
            }
            doc = Document(
                text=dto.analysis_result.strip(),
                metadata=metadata,
                id=str(uuid1())
            )
            dto_documents.append(doc)
    all_documents = pdf_documents + dto_documents
    vector_index = VectorStoreIndex.from_documents(all_documents)
    return vector_index.as_query_engine()


def query(question: str, query_engine: BaseQueryEngine) -> str:
    print("---------------------------------------")
    print(f"查询问题: {question}")
    answer = query_engine.query(question)
    print(f"AI回答: {answer}")
    print("---------------------------------------")
    return str(answer)
