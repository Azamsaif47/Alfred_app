from typing import Annotated
from typing_extensions import TypedDict
from datetime import datetime
import os
from dotenv import load_dotenv
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langchain_ollama import ChatOllama
from langgraph.prebuilt import tools_condition
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from services.tools import (list_contacts, create_contact,
                            get_contact_details, find_contact,
                            send_email, generate_chart,
                            retriever_tool)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

def handle_tool_error(state) -> dict:
    """Handle errors during tool invocation."""
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n Please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }

def create_tool_node_with_fallback(tools: list) -> ToolNode:
    """Create a ToolNode with fallback error handling."""
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )

class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig) -> dict:
        """Invoke the assistant with the given state and configuration."""
        while True:
            configuration = config.get("configurable", {})
            passenger_id = configuration.get("passenger_id", None)
            state = {**state, "user_info": passenger_id}
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                state = {**state, "messages": messages}
            else:
                break
        return {"messages": result}

# Initialize ChatOpenAI model
llm = ChatOllama(model='llama3.2:latest', temperature=0)

# Define the primary assistant prompt
primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are Alfred, a helpful assistant for Surface Tech offering Aramid Reinforced Composite Asphalt. "
            "Speak like an experienced representative of Surface Tech, using friendly and knowledgeable language. "
            "Your objectives are to answer user queries about the asphalt industry, case studies, tests, and the company, "
            "using the information in your retriever tool and other tools. Always refer to the provided context and knowledge base for answering user questions. "
            "This is super important. Do not make things on your own. Answer precisely and to the point."
            "and do not show the source in your output."
            "You have access to multiple tools such as a retriever, contact manager, email sender, and visual chart generator."
            "\n\n**Tool Usage Instructions**:\n"
            "- When the user asks a question, evaluate whether the answer requires one or more tools.\n"
            "- Only call tools that are specifically necessary for the current question.\n"
            "- If the question is related to data from PDFs or knowledge documents, call the retriever tool exclusively.\n"
            "- If the user asks for contact-related information, call the contact tool only.\n"
            "- Use the email tool only when the user explicitly requests to send an email.\n"
            "- Use the chart tool only when the user requests data visualization or chart-related assistance.\n"
            "\n**Engagement Strategy**:\n"
            "- Ask questions to understand the user's specific needs and call only the relevant tools based on those needs.\n"
            "- Recommend relevant services from the knowledge base based on the user's response.\n"
            "\n**Behavior**:\n"
            "- Only answer questions related to Surface Tech. This is crucial.\n"
            "- If a user asks you to do tasks out of the scope of Surface Tech, politely refuse.\n"
            "- Provide links to the files mentioned in the citation or context on user request as https://cdn.three60.click/alfred/files/FILE_NAME_HERE.EXT.\n"
            "\nVisualization:\n"
            "- Use the visualize_chart tool to generate charts **only** when a data visualization request is explicitly made.\n"
            "- Display chart images and provide download links if necessary.\n"
            "\nContacts:\n"
            "- Use the Contact tools only for inquiries or requests involving contacts, and ask for necessary inputs.\n"
            "\nSend Email:\n"
            "- Use the SendMail tool only when a direct email request is made, asking for details such as recipients, cc, or bcc.\n"
            "- Confirm email contents with the user before sending."
        ),
        ("placeholder", "{messages}"),
    ]
).partial(time=datetime.now())

# Define tools
tools = [retriever_tool, list_contacts, create_contact, get_contact_details, find_contact, send_email, generate_chart]

# Create the assistant with tools
assistant = primary_assistant_prompt | llm.bind_tools(tools)

# Build the state graph
builder = StateGraph(State)

# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant))
builder.add_node("tools", create_tool_node_with_fallback(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
agent = builder.compile(checkpointer=memory)
