import os
from uuid import uuid1
from typing import List
from llama_index.core import SimpleDirectoryReader, Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.indices.base import BaseQueryEngine
from dto.pdf_image_dto import pdf_image_dto
from llama_index.core import Settings
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.huggingface import HuggingFaceEmbedding

# import logging
# import sys
# open detail log, will show prompt
# logging.basicConfig(stream=sys.stdout, format="%(asctime)s %(message)s", level=logging.DEBUG, force=True)

llm = DeepSeek(model="deepseek-chat", api_key="sk-9b5776bd68e045f7ae2171077134b2a4")
Settings.llm = llm
Settings.embed_model = HuggingFaceEmbedding(model_name="BAAI/bge-small-en-v1.5")


def vector(file_id: str, file_path: str, dtos: List[pdf_image_dto]) -> BaseQueryEngine:
    persist_dir = "persist_dir"
    if os.path.exists(persist_dir) and os.path.isdir(persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)
        return index.as_query_engine()
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
    vector_index.storage_context.persist(persist_dir)
    return vector_index.as_query_engine()


def query(question: str, query_engine: BaseQueryEngine) -> str:
    print("---------------------------------------")
    print(f"Q: {question}")
    answer = query_engine.query(question)
    print(f"A: {answer}")
    print("---------------------------------------")
    return str(answer)
