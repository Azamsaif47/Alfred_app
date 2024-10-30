from typing import Annotated
from typing_extensions import TypedDict
from datetime import datetime
import os
from dotenv import load_dotenv
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import ToolMessage, SystemMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from mem0 import MemoryClient

# Local imports
from services.tools import (list_contacts, create_contact,
                            get_contact_details, find_contact,
                            send_email, generate_chart,
                            retriever_tool)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
MEMO_API_KEY = os.getenv('MEMO_API_KEY')
client = MemoryClient(api_key=MEMO_API_KEY)


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
    mem0_user_id: str

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
llm = ChatOpenAI(model_name='gpt-4o-2024-08-06', temperature=0)

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
            "in your retriever tool you have some documents which include different question related to Surface Tech. "
            "I want you to give 3 suggestions as a must with every output related to Surface Tech, represented after a line break of the output message."
            "The structure of suggested questions must be like this output then line break (crucial) then word suggestion and below suggested questions."
            "And send the suggested questions in another JSON then the message content."
            "When the user asks something about Surface Tech and you answer, also send some suggestions of questions according to that specific context."
            "\n\nEngagement Strategy:\n"
            "- Ask questions to understand the user's specific needs.\n"
            "- Recommend relevant services from the knowledge base based on the user's response.\n"
            "\nBehavior:\n"
            "- Only answer questions related to Surface Tech. This is crucial.\n"
            "- If a user asks you to do tasks out of the scope of Surface Tech, politely refuse.\n"
            "- Provide links to the files mentioned in the citation or context on user request as https://cdn.three60.click/alfred/files/FILE_NAME_HERE.EXT.\n"
            "\nVisualization:\n"
            "- Use the visualize_chart tool to generate different types of charts to visualize data for the user. "
            "Display the chart in an image with at least 500px of width.\n"
            "- Display 2 links below the chart image: one for view in full screen which opens the link in a new tab, "
            "and the second to force the browser to download the SVG.\n"
            "\nContacts:\n"
            "- Use the Contact tools to inquire, search for a person or contact, and create a new one by getting required inputs from the user.\n"
            "\nSend Email:\n"
            "- Use the SendMail tool to send emails. Ask the user for required inputs and confirm if they want to add cc or bcc.\n"
            "- Query the user suggested contacts if they provided names only.\n"
            "- Ask for email addresses from the user if the requested contacts are not available.\n"
            "- Show a final draft of the email with recipients, cc, and bcc before sending it."
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


messages = [
    {"role": "user", "content": "Hi, I'm Alex. I'm a vegetarian and I'm allergic to nuts."},
    {"role": "assistant", "content": "Hello Alex! I've noted that you're a vegetarian and have a nut allergy. I'll keep this in mind for any food-related recommendations or discussions."}
]
client.add(messages, user_id="43bff7c7-c71b-4fae-bccf-405bcb6b263d")

memories = client.search(messages[-1]['content'], user_id="43bff7c7-c71b-4fae-bccf-405bcb6b263d")

context = "Relevant information from previous conversations:\n"
for memory in memories:
    context += f"- {memory['memory']}\n"

# Move this part outside the loop
system_message = SystemMessage(content=f"""You are a helpful customer support assistant. Use the provided context to personalize your responses and remember user preferences and past interactions.
{context}""")

question = "do you know my name"

messages.append({"role": "user", "content": question})

client.add(messages, user_id="43bff7c7-c71b-4fae-bccf-405bcb6b263d")

full_messages = [system_message] + messages


# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant))
builder.add_node("tools", create_tool_node_with_fallback(tools))

# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges("assistant", tools_condition)
builder.add_edge("tools", "assistant")



memory = MemorySaver()
agent = builder.compile(checkpointer=memory)

response = agent.invoke(
    {"messages": full_messages},  # Send all messages including the custom question
    config={"configurable": {"thread_id": "43bff7c7-c71b-4fae-bccf-405bcb6b263d", "thread_name": "updated_chat_name"}}
)

final_response = ""

# Iterate through the messages in the response
for message in response['messages']:
    # Check if the message is of type AIMessage
    if isinstance(message, AIMessage):
        # Extract the content of the last AIMessage
        final_response = message.content  # This holds the main response text

# Print the final extracted response
print(f"Assistant's Response: {final_response}")