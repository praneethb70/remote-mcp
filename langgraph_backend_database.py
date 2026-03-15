from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from typing import TypedDict,Annotated
from langgraph.graph import StateGraph, START, END
# from langgraph.checkpoint.memory import InMemorySaver
# from langchain_google_genai import GoogleGenerativeAI
from langgraph.graph.message import add_messages
from langchain_groq import ChatGroq

import sqlite3

# from langgraph.checkpoint.serde.encrypted import EncryptedSerializer
from langgraph.checkpoint.sqlite import SqliteSaver
import os

db_path = os.getenv("CHECKPOINT_DB_PATH", "checkpoint.db")
checkpointer = SqliteSaver(sqlite3.connect(db_path, check_same_thread=False))
# serde = EncryptedSerializer.from_pycryptodome_aes()  # reads LANGGRAPH_AES_KEY
# checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db"), serde=serde)
# checkpointer = SqliteSaver(sqlite3.connect("checkpoint.db",check_same_thread=False))

from dotenv import load_dotenv
load_dotenv()

# langfuse_client.py
import os
# from langfuse import Langfuse

# langfuse = Langfuse(
#     secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
#     public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
#     host=os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com"),
# )

llm = ChatGroq(
    model="qwen/qwen3-32b",
    temperature=0,
    max_tokens=None,
    reasoning_format="parsed",
    timeout=None,
    max_retries=2,
    # other params...
    api_key=os.getenv("GROQ_API_KEY")
)



# model = GoogleGenerativeAI(model="gemini-2.5-flash")
class ChatState(TypedDict):
    # messages: list
    messages:Annotated[list[BaseMessage],add_messages]


# def chat_node(state:ChatState):
#     response = llm.invoke(state["messages"])
#     return {"messages": [response]}

# from langfuse_client import langfuse  # ADD THIS

def chat_node(state: ChatState):
    user_messages = state["messages"]
    last_user_message = user_messages[-1].content

    # --- LLM call ---
    response = llm.invoke(user_messages)

    # --- Minimal Langfuse logging (new API) ---
    # generation = langfuse.generation(
    #     name="chatbot-generation",
    #     model="qwen/qwen3-32b",
    #     input=last_user_message,
    #     output=response.content,
    # )
    # generation.end()

    return {"messages": [response]}
# checkpointer=InMemorySaver()

graph=StateGraph(ChatState)

graph.add_node(chat_node,'chat_node')

graph.add_edge(START, 'chat_node')
graph.add_edge('chat_node', END)

chatbot = graph.compile(checkpointer=checkpointer)

def retrieve_all_threads():
    all_threads = set()
    for checkpoint in checkpointer.list(None):
        thread=checkpoint.config['configurable']['thread_id']
        all_threads.add(thread)
    return list(all_threads)