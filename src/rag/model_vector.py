import os
from urllib.parse import quote
from uuid import uuid1
from typing import List
from typing import Generator
from llama_index.core import Document, VectorStoreIndex, StorageContext, load_index_from_storage
from llama_index.core.indices.base import BaseQueryEngine
from dto.pdf_image_dto import pdf_image_dto
from llama_index.core import Settings
from llama_index.llms.deepseek import DeepSeek
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.readers.file import PDFReader
from llama_index.core.query_engine import RetrieverQueryEngine
from llama_index.core.retrievers import VectorIndexRetriever
from llama_index.core.postprocessor import SentenceTransformerRerank
from pathlib import Path
from rag.model_pdf_table_loader import load_tables_with_pageinfo

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
    print("vector:" + file_name)
    persist_dir = "persist_dir"
    os.environ["PATH"] += os.pathsep + r"C:\Program Files\gs\gs10.06.0\bin"

    text_reader = PDFReader()
    text_docs = text_reader.load_data(file=Path(file_path))

    table_docs = load_tables_with_pageinfo(file=Path(file_path), pages="all")
    pdf_documents = text_docs + table_docs

    enhanced_pdf_docs = []
    for doc in pdf_documents:
        page_num = doc.metadata.get("page_label") or doc.metadata.get("page_number", "unknown")
        doc.id_ = str(uuid1())
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
                "pdf_source_path": file_path,
                "image_path": dto.image_path
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
        vector_index = load_index_from_storage(storage_context)
        for ref_doc_id, ref_doc_info in vector_index.ref_doc_info.items():
            if ref_doc_info.metadata.get("file_id") == file_id:
                print("delete file:" + file_name)
                print("delete ref doc:" + ref_doc_info.to_json())
                vector_index.delete_ref_doc(ref_doc_id, delete_from_docstore=True)
        print("insert file:" + file_name)
        vector_index.insert_nodes(all_documents)
        vector_index.storage_context.persist(persist_dir)
        return create_query_engine(vector_index)
    print("init store dir")
    vector_index = VectorStoreIndex.from_documents(all_documents)
    vector_index.storage_context.persist(persist_dir)
    return create_query_engine(vector_index)


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
    added_items = set()
    for i, node in enumerate(answer.source_nodes, 1):
        file_id = node.node.metadata.get('file_id', 'unknown')
        file_name = node.node.metadata.get('file_name', 'unknown')
        source_type = node.node.metadata.get('source_type', 'unknown')
        page_number = node.node.metadata.get('page_number', 'unknown')
        file_link = f"https://docs.google.com/document/d/{file_id}/view"
        unique_key = f"{file_id}_{str(page_number)}"
        if unique_key not in added_items:
            ref = f'<a href="{quote(file_link, safe=":/")}" target="_blank" class="text-primary hover:underline">{file_name}</a> - page {page_number}'
            if "pdf_image" == source_type:
                image_path = "http://localhost:5000/pic/" + node.node.metadata.get('image_path', 'unknown')
                print(image_path)
                image_html = (
                    f'<span class="ml-2 mr-1 inline-block align-middle">'
                    f'<img src="{quote(image_path, safe=":/")}" '
                    f'alt="Preview of {file_name} page {page_number}" '
                    f'class="pdf-preview-img cursor-zoom-in border border-gray-200 rounded-md" '
                    f'data-full-src="{quote(image_path, safe=":/")}" '
                    f'style="max-width: 80px; max-height: 120px; object-fit: contain;" '
                    f'onclick="showImageModal(this)">'
                    f'</span>'
                )
                ref += image_html
            sources.append(ref)
            added_items.add(unique_key)

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


def create_rank_query_engine(index: VectorStoreIndex) -> BaseQueryEngine:
    retriever = VectorIndexRetriever(
        index=index,
        similarity_top_k=10
    )

    reranker = SentenceTransformerRerank(
        model="BAAI/bge-reranker-large",
        top_n=3
    )

    return RetrieverQueryEngine.from_args(
        retriever=retriever,
        node_postprocessors=[reranker],
        streaming=True
    )


def create_query_engine(index: VectorStoreIndex) -> BaseQueryEngine:
    return index.as_query_engine(similarity_top_k=3, streaming=True)
