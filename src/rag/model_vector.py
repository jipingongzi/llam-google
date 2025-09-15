import os
from uuid import uuid1
from typing import List
from typing import Generator
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
Settings.embed_model = HuggingFaceEmbedding(
    model_name="BAAI/bge-large-en-v1.5",
    max_length=512
)


def vector(file_id: str, file_path: str, file_name: str, dtos: List[pdf_image_dto]) -> BaseQueryEngine:
    persist_dir = "persist_dir"
    pdf_documents = SimpleDirectoryReader(input_files=[file_path]).load_data()
    enhanced_pdf_docs = []
    for doc in pdf_documents:
        page_num = doc.metadata.get("page_label") or doc.metadata.get("page_number", "unknown")
        doc.metadata.update({
            "file_id": file_id,
            "file_name": file_name,
            "page_number": page_num,
            "source_type": "pdf_text",
            "pdf_source_path": file_path
        })
        enhanced_pdf_docs.append(doc)
    dto_documents = []
    for dto in dtos:
        if dto.analysis_result and dto.analysis_result.strip():
            metadata = {
                "file_id": file_id,
                "file_name": file_name,
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
    all_documents = enhanced_pdf_docs + dto_documents
    if os.path.exists(persist_dir) and os.path.isdir(persist_dir):
        storage_context = StorageContext.from_defaults(persist_dir=persist_dir)
        index = load_index_from_storage(storage_context)
        for ref_doc_id, ref_doc_info in index.ref_doc_info.items():
            print(ref_doc_id)
            print(ref_doc_info.to_json())
            if ref_doc_info.metadata.get("file_id") == file_id:
                print("delete doc:" + ref_doc_info.to_json())
                index.delete_ref_doc(ref_doc_id, delete_from_docstore=True)
        index.insert_nodes(all_documents)
        return index.as_query_engine(similarity_top_k=5, streaming=True)
    vector_index = VectorStoreIndex.from_documents(all_documents)
    vector_index.storage_context.persist(persist_dir)
    return vector_index.as_query_engine(similarity_top_k=5, streaming=True)


def query(question: str, query_engine: BaseQueryEngine) -> Generator[str, None, None]:
    print("\n---------------------------------------")
    print(f"Q: {question}")
    answer = query_engine.query(question)
    # answer.print_response_stream()
    print("\n\nsource：")
    for i, node in enumerate(answer.source_nodes, 1):
        print(
            f"{i}. file id: {node.node.metadata.get('file_id', 'unknown')}, "
            f"file name: {node.node.metadata.get('file_name', 'unknown')}, "
            f"PDF page: {node.node.metadata.get('page_number', 'unknown')}, "
            f"source type: {node.node.metadata.get('source_type', 'unknown')}, "
            f"score: {node.score:.4f}"
        )
    full_answer = []
    for token in answer.response_gen:
        full_answer.append(token)
        yield token
    sources = []
    print("\n\nsource：")
    for i, node in enumerate(answer.source_nodes, 1):
        file_id = node.node.metadata.get('file_id', 'unknown')
        file_name = node.node.metadata.get('file_name', 'unknown')
        page_number = node.node.metadata.get('page_number', 'unknown')
        file_link = f"https://docs.google.com/document/d/{file_id}/view"
        print(
            f"{i}. file id: {node.node.metadata.get('file_id', 'unknown')}, "
            f"file name: {file_name}, "
            f"PDF page: {page_number}, "
            f"source type: {node.node.metadata.get('source_type', 'unknown')}, "
            f"score: {node.score:.4f}"
        )
        sources.append(f"[{file_name}]({file_link}) - page {page_number}")

    if sources:
        yield "\n\nReference:"
        for source in sources:
            yield f"\n- {source}"

    return


def query_print(question: str, query_engine: BaseQueryEngine):
    print("\n---------------------------------------")
    print(f"Q: {question}")
    answer = query_engine.query(question)
    answer.print_response_stream()
    print("\n\nsource：")
    for i, node in enumerate(answer.source_nodes, 1):
        print(
            f"{i}. file id: {node.node.metadata.get('file_id', 'unknown')}, "
            f"file name: {node.node.metadata.get('file_name', 'unknown')}, "
            f"PDF page: {node.node.metadata.get('page_number', 'unknown')}, "
            f"source type: {node.node.metadata.get('source_type', 'unknown')}, "
            f"score: {node.score:.4f}"
        )
