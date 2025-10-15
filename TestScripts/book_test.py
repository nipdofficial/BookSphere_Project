from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma

# Initialize HuggingFace embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# Example usage with Chroma
texts = ["This is a book about AI.", "This is a novel about love."]
db = Chroma.from_texts(texts, embeddings, persist_directory="db_books")

# Test search
query = "romantic stories"
results = db.similarity_search(query, k=1)
print(results)
