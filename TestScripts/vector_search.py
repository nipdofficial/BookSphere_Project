from langchain_community.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings  # updated import
from langchain_community.vectorstores import FAISS

# 1. Load a document
loader = TextLoader(r"C:\Users\MSI\Desktop\Book Sphere\data\sample.txt", encoding="utf-8")
docs = loader.load()

# 2. Split text into chunks
splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
documents = splitter.split_documents(docs)

# 3. Create embeddings
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")

# 4. Store in FAISS
db = FAISS.from_documents(documents, embeddings)

# 5. Test search
query = "What is this document about?"
results = db.similarity_search(query, k=2)

for r in results:
    print(r.page_content)


