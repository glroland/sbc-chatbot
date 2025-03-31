import streamlit as st
import random
import time
import torch
from openai import OpenAI
from pymilvus import MilvusClient
from sentence_transformers import SentenceTransformer

OPENAI_URL = "http://envision:11434/v1"
OPENAI_KEY = "not_used"
OPENAI_TIMEOUT = 1000
OPENAI_MODEL = "llama3.2"
OPENAI_TEMPERATURE = 0.8
OPENAI_MAX_TOKENS = 1000
OPENAI_TOP_P = 1.0
MILVUS_URL = "http://db:19530"
MILVUS_TOKEN = "root:Milvus"
VDB_DB_NAME = "sbcchatbot"
VDB_COLLECTION_MD = "sbcmd"
EMBEDDINGS_MODEL = "sentence-transformers/all-mpnet-base-v2"

INTRO_MESSAGE = "How can I help you better understand your medical insurance benefits and coverages?"
SYSTEM_PROMPT = """You are an expert in the medical insurance industry and are tasked with answering questions about SBC documentation.  SBC documents are summaries of benefits and coverage that are required to be provided to consumers by health insurance companies.  You are to answer questions submitted by the user about medical insurance only.  All responses must be based on the SBC documentation provided in the system prompt.  If you do not know the answer, please say 'I don't know'.  

SBC Document Contents:
"""

torch.classes.__path__ = []

openai_client = OpenAI(
    base_url = OPENAI_URL, 
    api_key =OPENAI_KEY,
    timeout = OPENAI_TIMEOUT)

vdb_client = MilvusClient(
    uri=MILVUS_URL,
    token=MILVUS_TOKEN
)
vdb_client.using_database(VDB_DB_NAME)
vdb_client.load_collection(collection_name=VDB_COLLECTION_MD)

model = SentenceTransformer(EMBEDDINGS_MODEL)

st.set_page_config(page_title="Ask SBC Anything", page_icon=":smiley:", layout="wide")

st.title("Ask an SBC Document Anything!")

st.write("""To help consumers compare the different features of health benefits and coverage, the Affordable Care Act generally requires all group health plans and health insurance companies to provide individuals a “summary of benefits and coverage” that “accurately describes the benefits and coverage under the plan. The SBC is a snapshot of a health plan’s costs, benefits, covered health care services, and other features that are important to consumers. SBCs also explain health plans’ unique features like cost sharing rules and include significant limits and exceptions to coverage in easy-tounderstand terms.""")

file_keys = vdb_client.query(
    collection_name=VDB_COLLECTION_MD,
    filter="file like '%'",
    output_fields=["file"],
    limit=3
)
print (f"File Keys [{len(file_keys)}]: {file_keys}")
file_list = []
for file_key in file_keys:
    file_list.append(file_key["file"])

def on_sbc_selectbox_change():
    print ("INFO ---- SBC Selectbox Value Changed by User!")
    del st.session_state["messages"]

option = st.selectbox(
    "Which Summary of Benefits and Coverage document would you like to chat with?",
    file_list,
    on_change=on_sbc_selectbox_change
)

# Initialize chat history
if "messages" not in st.session_state:
    system_prompt_full = SYSTEM_PROMPT

    texts = vdb_client.query(
        collection_name=VDB_COLLECTION_MD,
        filter="file like '%'",
        output_fields=["text"],
        limit=1
    )
    system_prompt_full += texts[0]["text"]

    st.session_state.messages = [{"role": "system", "content": system_prompt_full}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    if message["role"] == "system":
        with st.chat_message("assistant"):
            st.markdown(INTRO_MESSAGE)
    else:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("Type your question here..."):
    print (f"Prompt: {prompt}")

    # Add user message to chat history
    st.session_state.messages.append({"role": "user", "content": prompt})
    # Display user message in chat message container
    with st.chat_message("user"):
        st.markdown(prompt)

    # Display assistant response in chat message container
    with st.chat_message("assistant"):
        response_st = st.empty()
    
        print ("BEFORE")
        # seek response from the llm
        completion = openai_client.chat.completions.create(
            model = OPENAI_MODEL,
            messages = st.session_state.messages,
            temperature = OPENAI_TEMPERATURE,
            max_tokens = OPENAI_MAX_TOKENS,
            top_p = OPENAI_TOP_P
        )
        assistant_response = completion.choices[0].message.content
        response_st.markdown(assistant_response)
        print (f"RESPONSE: {assistant_response}")

    # Add assistant response to chat history
    st.session_state.messages.append({"role": "assistant", "content": assistant_response})
    print (f"HISTORY: {st.session_state.messages}")
