import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

# ✅ Updated imports for LangChain 0.2+
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import PromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableParallel, RunnablePassthrough, RunnableLambda
from langchain_core.output_parsers import StrOutputParser
from fastapi.concurrency import run_in_threadpool

# ===============================
# 🔑 GOOGLE API KEY
# ===============================
os.environ["GOOGLE_API_KEY"] = "AIzaSyCijx-P_9GUs6F75rwL7iN00dV3w7mlUnw"

# ===============================
# 🚀 FASTAPI SETUP
# ===============================
app = FastAPI(title="Dynamic YouTube Q&A Backend (Hindi + English)")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===============================
# 📩 Request Model
# ===============================
class QuestionRequest(BaseModel):
    video_id: str
    question: str

# ===============================
# 💬 Initialize LLM
# ===============================
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash")

# ===============================
# 🧠 Prompt Template
# ===============================
prompt = PromptTemplate(
    template="""
You are a helpful AI assistant.
Answer the question based on the given YouTube video transcript.
Make sure each bullet point starts with '*'.
If the question cannot be answered, say you don't know.

{context}

Question:
{question}
""",
    input_variables=["context", "question"]
)

# ===============================
# 🎥 Fetch Transcript
# ===============================
def fetch_transcript(video_id: str):
    try:
        transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=["hi"])
    except Exception:
        try:
            transcript_list = YouTubeTranscriptApi().fetch(video_id, languages=["en"])
        except TranscriptsDisabled:
            raise HTTPException(status_code=404, detail="Transcripts are disabled for this video.")
        except NoTranscriptFound:
            raise HTTPException(status_code=404, detail="No transcript found in Hindi or English.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching English transcript: {e}")
    transcript_text = " ".join(snippet.text for snippet in transcript_list)
    return transcript_text

# ===============================
# 🧩 Create Dynamic Vector Store
# ===============================
def create_dynamic_vector_store(transcript: str):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    chunks = splitter.create_documents([transcript])
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    vector_store = FAISS.from_documents(chunks, embeddings)
    return vector_store.as_retriever(search_type="similarity", search_kwargs={"k": 3})

# ===============================
# ⚡ Cache Retrievers for Performance
# ===============================
VECTOR_STORE_CACHE = {}
def get_retriever(transcript, video_id):
    if video_id in VECTOR_STORE_CACHE:
        return VECTOR_STORE_CACHE[video_id]
    retriever = create_dynamic_vector_store(transcript)
    VECTOR_STORE_CACHE[video_id] = retriever
    return retriever

# ===============================
# 💬 /ask Endpoint
# ===============================
@app.post("/ask")
async def ask_question(request: QuestionRequest):
    transcript_text = fetch_transcript(request.video_id)
    retriever = get_retriever(transcript_text, request.video_id)
    
    parallel_chain = RunnableParallel({
        "context": retriever | RunnableLambda(lambda docs: "\n\n".join(d.page_content for d in docs)),
        "question": RunnablePassthrough()
    })
    
    parser = StrOutputParser()
    main_chain = parallel_chain | prompt | llm | parser
    
    # Run in threadpool for async safety
    answer_text = await run_in_threadpool(lambda: main_chain.invoke(request.question))
    
    # Format bullet points
    formatted_answer = "\n".join(
        [line if line.strip().startswith("*") else f"* {line.strip()}" for line in answer_text.split("\n") if line.strip()]
    )
    
    return {"answer": formatted_answer}

# ===============================
# ❤️ Health Check
# ===============================
@app.get("/health")
async def health():
    return {"status": "ok"}
