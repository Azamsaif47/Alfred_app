import requests
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain_ollama import ChatOllama
from langchain_ollama import OllamaEmbeddings
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from json_repair import repair_json
from langchain import hub
import os

load_dotenv()

CONTACTS_URL = os.getenv('CONTACTS_URL')
CHART_URL = os.getenv('CHART_URL')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


embed = OpenAIEmbeddings()


vectorstore = FAISS.load_local(
    folder_path = os.path.join(BASE_DIR, "Vector_store", "new_alfred"),
    embeddings=embed,
    index_name="faiss.index",
    allow_dangerous_deserialization=True
)

prompt = hub.pull("langchain-ai/retrieval-qa-chat")

llm = ChatOllama(model='llama3.2:latest', temperature=0)

combine_docs_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), combine_docs_chain)


@tool
def retriever_tool(query: str = None):
    """This tool contains all the necessary data about
       Surface Tech's offering of Aramid Reinforced Composite Asphalt.
       When a user asks a question about this topic, always use this tool to retrieve the
       information and answer their question. Be sure to include the source provided in the JSON format with your answer,
       as the source is essential for accuracy.
    """
    print("retriever_tool is called")
    print(f"llm question from tool {query}")
    llm_response = rag_chain.invoke({"input": query})
    response = repair_json(str(llm_response))
    print(f"the tool response {response}")
    return response

question = "what is virgin binders and why it is used in aramid fiber"
res = retriever_tool(question)
print(res)