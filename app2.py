import os
import re
import streamlit as st
from dotenv import load_dotenv
from groq import Groq

# Load environment variables
load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# ------------------------------
# Agent Class
# ------------------------------
class Agent:
    def __init__(self, client: Groq, system: str = "") -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        result = self.execute()
        self.messages.append({"role": "assistant", "content": result})
        return result

    def execute(self):
        completion = self.client.chat.completions.create(
            model="llama3-70b-8192",
            messages=self.messages
        )
        return completion.choices[0].message.content

# ------------------------------
# Tools
# ------------------------------
def calculate(operation: str) -> float:
    return eval(operation)

def get_planet_mass(planet) -> float:
    match planet.lower():
        case "earth":
            return 5.972e24
        case "jupiter":
            return 1.898e27
        case "mars":
            return 6.39e23
        case "mercury":
            return 3.285e23
        case "neptune":
            return 1.024e26
        case "saturn":
            return 5.683e26
        case "uranus":
            return 8.681e25
        case "venus":
            return 4.867e24
        case _:
            return 0.0

# ------------------------------
# System Prompt
# ------------------------------
system_prompt = """
You run in a loop of Thought, Action, PAUSE, Observation.
At the end of the loop you output an Answer
...
Answer: The mass of Earth times 2 is 1,1944×10e25.
Now it's your turn:
""".strip()

# ------------------------------
# Agent Loop
# ------------------------------
def agent_loop(query: str, max_iterations=20):
    agent = Agent(client=client, system=system_prompt)
    tools = ["calculate", "get_planet_mass"]
    next_prompt = query
    i = 0

    while i < max_iterations:
        i += 1
        result = agent(next_prompt)

        if "PAUSE" in result and "Action" in result:
            action = re.findall(r"Action: ([a-z_]+): (.+)", result, re.IGNORECASE)
            if action:
                chosen_tool = action[0][0]
                arg = action[0][1].strip()

                if chosen_tool in tools:
                    result_tool = eval(f"{chosen_tool}('{arg}')")
                    next_prompt = f"Observation: {result_tool}"
                else:
                    next_prompt = "Observation: Tool not found"
            continue

        if "Answer" in result:
            return result

    return "Sorry, I couldn't find an answer."

# ------------------------------
# Streamlit Chat UI
# ------------------------------
st.set_page_config(page_title="Agentic AI Chat", page_icon="🤖")

st.title("🤖 Welcome to Kepler Agent")

# Store chat history
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input box
if prompt := st.chat_input("Ask me anything..."):
    # Add user query
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Run agent
    response = agent_loop(prompt)

    # Add agent response
    st.session_state.messages.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.markdown(response)

