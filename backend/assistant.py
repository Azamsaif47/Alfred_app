from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import AnyMessage, add_messages
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START
from langgraph.prebuilt import tools_condition
from datetime import datetime
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from chat_app.backend.chatbot_tools import list_contacts,create_contact, get_contact_details, find_contact, send_email, generate_chart, retriever_tool
from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')




def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )



class State(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]



class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: State, config: RunnableConfig):
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

llm = ChatOpenAI(model_name='gpt-4o-2024-08-06', temperature=0)

primary_assistant_prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are chatbot, a helpful assistant for a company (your comany name here)"
            "Speak like an experienced representative of [Company name], using friendly and knowledgeable language. "
            "Your objectives are to answer user queries about the asphalt industry, case studies, tests, and the company, "
            "using the information in your retriever tool and other tools. Always refer to the provided context and knowledge base for answering user questions. "
            "This is super important. Do not make things on your own. Answer precisely and to the point."
            "and do not show the source in your output"
            "in your retriever tool you have some documents which include different question related to [Company name] "
            "i want you give 3 messages must as a sugggestion with every output related to [Company name] it should be represent after a line break of output message"
            "the structure of suggestion questions must be like this output then line break(crucial) then word suggestion and below suggested questions"
            "and send the suggested question in another json then the message content"
            "when user ask something about [Company name] and you answer that also send some suggestion of questions according to that specific context"
            "\n\nEngagement Strategy:\n"
            "- Ask questions to understand the user's specific needs.\n"
            "- Recommend relevant services from the knowledge base based on the user's response.\n"
            "\nBehavior:\n"
            "- Only answer questions related to [Company name]. This is crucial.\n"
            "- If a user asks you to do tasks out of scope of [Company name], politely refuse.\n"
            "- Provide the links to the files mentioned in the citation or context on user request as your-url-for-api\n"
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


tools = [retriever_tool, list_contacts, create_contact, get_contact_details, find_contact, send_email, generate_chart]

assistant = primary_assistant_prompt | llm.bind_tools(tools)



builder = StateGraph(State)


# Define nodes: these do the work
builder.add_node("assistant", Assistant(assistant))
builder.add_node("tools", create_tool_node_with_fallback(tools))
# Define edges: these determine how the control flow moves
builder.add_edge(START, "assistant")
builder.add_conditional_edges(
    "assistant",
    tools_condition,
)
builder.add_edge("tools", "assistant")

# The checkpointer lets the graph persist its state
# this is a complete memory for the entire graph.
memory = MemorySaver()
agent = builder.compile(checkpointer=memory)


