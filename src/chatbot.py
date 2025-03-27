import streamlit as st
import random
import time
from openai import OpenAI

OPENAI_URL = "http://envision:11434/v1"
OPENAI_KEY = "not_used"
OPENAI_TIMEOUT = 1000
OPENAI_MODEL = "llama3.2"
OPENAI_TEMPERATURE = 0.8
OPENAI_MAX_TOKENS = 1000
OPENAI_TOP_P = 1.0

SYSTEM_PROMPT = ""

openai_client = OpenAI(
    base_url = OPENAI_URL, 
    api_key =OPENAI_KEY,
    timeout = OPENAI_TIMEOUT)

st.set_page_config(page_title="Ask SBC Anything", page_icon=":smiley:", layout="wide")

st.title("Ask Summary of Benefits and Coverage (SBC) Anything!")

st.write("""To help consumers compare the different features of health benefits and coverage, the Affordable Care Act generally requires all group health plans and health insurance companies to provide individuals a “summary of benefits and coverage” that “accurately describes the benefits and coverage under the plan. The SBC is a snapshot of a health plan’s costs, benefits, covered health care services, and other features that are important to consumers. SBCs also explain health plans’ unique features like cost sharing rules and include significant limits and exceptions to coverage in easy-tounderstand terms.""")

# Initialize chat history
if "messages" not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Let's start chatting! 👇"}]

# Display chat messages from history on app rerun
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Accept user input
if prompt := st.chat_input("What is up?"):
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
