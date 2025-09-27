from langchain.chains import RetrievalQA
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.document_loaders import TextLoader
from langchain_community.vectorstores import FAISS
from langchain_openai import OpenAIEmbeddings, ChatOpenAI


# 1. Load your document
loader = TextLoader("my_notes.txt")   # replace with your file
documents = loader.load()

# 2. Split into chunks
splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
docs = splitter.split_documents(documents)

# 3. Embed + store in vector DB
embeddings = OpenAIEmbeddings()
vectorstore = FAISS.from_documents(docs, embeddings)

# 4. Create retriever
retriever = vectorstore.as_retriever()

# 5. Build RAG chain (retrieval + LLM)
qa = RetrievalQA.from_chain_type(
    llm=ChatOpenAI(model="gpt-4o-mini"),
    retriever=retriever,
    return_source_documents=True
)

# 6. Ask a question
query = "Summarize the main idea of this document."
result = qa({"query": query})

print("Answer:", result["result"])
print("\nSources:", result["source_documents"])
