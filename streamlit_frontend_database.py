import streamlit as st
from langgraph_database_backend import chatbot, retrieve_all_threads
# from langgraph_tool_backend import chatbot, retrieve_all_threads
# from chatbot_async import chatbot, retrieve_all_threads
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import uuid

#********************************Utility Functions***************************************

def generate_threadid():
    thread_id = uuid.uuid4()
    return thread_id

def reset_chat():
    st.session_state['message_history'] = []
    st.session_state['thread_id'] = generate_threadid()
    add_thread(st.session_state['thread_id'])

def add_thread(thread_id):
    if thread_id not in [t['thread_id'] for t in st.session_state['chat_threads']]:
        st.session_state['chat_threads'].append({'thread_id': thread_id, 'title': 'Untitled Conversation'})

def load_conversation(thread_id):
    return chatbot.get_state(config = {'configurable':{'thread_id': thread_id}}).values.get('messages', [])

#********************************Session Management***************************************

if 'message_history' not in st.session_state:
    st.session_state['message_history'] = []

if 'thread_id' not in st.session_state:
    st.session_state['thread_id'] = generate_threadid()

if 'chat_threads' not in st.session_state:
    thread_ids = retrieve_all_threads()  # returns set
    st.session_state['chat_threads'] = [
        {"thread_id": t_id, "title": "Untitled Conversation"}
        for t_id in thread_ids
    ]
    # st.session_state['chat_threads'] = retrieve_all_threads()

add_thread(st.session_state['thread_id'])




# *********************************Sidebar UI***************************************

st.sidebar.title("Langgraph Chatbot")

if st.sidebar.button("New Chat"):
    reset_chat()

st.sidebar.header("My Conversations")

# st.sidebar.text(st.session_state['thread_id'])

for thread in st.session_state['chat_threads'][::-1]:
    if st.sidebar.button(thread['title'], key=str(thread['thread_id'])):
        st.session_state['thread_id'] = thread['thread_id']
        messages = load_conversation(thread['thread_id'])

        temp_message_history = []

        for msg in messages:
            if isinstance(msg, HumanMessage):
                role = 'user'
            else:
                role = 'assistant'
            temp_message_history.append({'role': role, 'content': msg.content})

        st.session_state['message_history'] = temp_message_history

#********************************Main Chat UI***************************************

config = {'configurable':{'thread_id':st.session_state['thread_id']}}

for message in st.session_state['message_history']:
    with st.chat_message(message['role']):
        st.text(message['content'])

user_input = st.chat_input("Type here...")

if user_input:
    st.session_state['message_history'].append({'role':'user','content':user_input})
    for t in st.session_state['chat_threads']:
        if t['thread_id'] == st.session_state['thread_id'] and t['title'] == "Untitled Conversation":
            t['title'] = user_input[:40]
    with st.chat_message('user'):
        st.text(user_input)

    with st.chat_message('assistant'):
        ai_message =st.write_stream(
        chunk.content for chunk,metadata in chatbot.stream(
            {'messages': [HumanMessage(content=user_input)]},
            config = config,
            stream_mode = 'messages'
        )
        )
    st.session_state['message_history'].append({'role':'assistant','content':ai_message})





# st.chat_message is used to display the messages in the chat interface. We use it to display both the user's input and the assistant's response. The role parameter is set to 'user' for user messages and 'assistant' for assistant messages, which helps to differentiate them in the chat interface.  

# st.text is used to display the content of the messages in the chat interface. 

# st.chat_input is used to create an input field for the user to type their messages.

# st.write_stream is used to stream the response from the chatbot in real-time. It takes a generator expression that yields the content of each chunk as it is received from the chatbot's stream method. The stream_mode is set to 'messages' to indicate that we want to receive the response in message format. The ai_message variable will hold the final content of the assistant's response after the streaming is complete.

# st.session_state is used to maintain the state of the chat history across interactions. We store the message history in st.session_state['message_history'], which allows us to persist the conversation history as the user interacts with the chatbot. This way, we can display the entire conversation history in the chat interface and ensure that it is preserved even when new messages are added.




