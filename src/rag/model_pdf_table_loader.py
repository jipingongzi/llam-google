import camelot
from pathlib import Path
from llama_index.core.schema import Document


def load_tables_with_pageinfo(file: Path, pages: str = "1") -> list[Document]:
    results = []

    try:
        tables = camelot.read_pdf(
            filepath=str(file),
            pages=pages,
            flavor="lattice"
        )

        if pages.lower() == "all":
            page_list = [str(table.page) for table in tables]
        else:
            page_ranges = pages.split(",")
            page_list = []
            for r in page_ranges:
                if "-" in r:
                    start, end = r.split("-")
                    page_list.extend(str(p) for p in range(int(start), int(end) + 1))
                else:
                    page_list.append(r)

        for idx, table in enumerate(tables):
            page_num = page_list[idx] if idx < len(page_list) else str(table.page)
            table_markdown = table.df.to_markdown(index=False)
            doc = Document(
                text=table_markdown,
                metadata={
                    "page_number": page_num,
                    "table_index": idx + 1,
                    "file_path": str(file),
                    "source_type": "pdf_table",
                    "extraction_method": "camelot_lattice"
                }
            )
            results.append(doc)

    except Exception as e:
        print(f"error: {str(e)}")

    return results


if __name__ == "__main__":
    pdf_path = Path("your_document.pdf")
    tables = load_tables_with_pageinfo(pdf_path, pages="all")

    for doc in tables:
        print(f"page: {doc.metadata['page_number']}, table {doc.metadata['table_index']}:")
        print(doc.text[:200])
        print("-" * 50)
