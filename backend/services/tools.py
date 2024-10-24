import requests
from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_openai import ChatOpenAI
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from dotenv import load_dotenv
from json_repair import repair_json
from langchain import hub
import os

load_dotenv()

CONTACTS_URL = os.getenv('CONTACTS_URL')
CHART_URL = os.getenv('CHART_URL')

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))



vectorstore = FAISS.load_local(
    folder_path = os.path.join(BASE_DIR, "Vector_store", "new_alfred"),
    embeddings=OpenAIEmbeddings(),
    index_name="faiss.index",
    allow_dangerous_deserialization=True
)

prompt = hub.pull("langchain-ai/retrieval-qa-chat")

llm = ChatOpenAI(model_name='gpt-4o-2024-08-06', temperature=0)

combine_docs_chain = create_stuff_documents_chain(llm, prompt)
rag_chain = create_retrieval_chain(vectorstore.as_retriever(), combine_docs_chain)

import time


@tool
def retriever_tool(query: str = None):
    """This tool contains all the necessary data about
       Surface Tech's offering of Aramid Reinforced Composite Asphalt.
       When a user asks a question about this topic, always use this tool to retrieve the
       information and answer their question. Be sure to include the source provided in the JSON format with your answer,
       as the source is essential for accuracy.
    """

    llm_response = rag_chain.invoke({"input": query})
    response = repair_json(str(llm_response))
    return response


@tool
def list_contacts(search: str = None):
    """
    List contacts via the Alfred API using Bearer token authentication.

    Args:
        search (str): Optional search query to filter contacts.

    Returns:
        dict: API response as JSON.
    """
    api_base_url = CONTACTS_URL
    token = "2|uDd2aZH3gFZgNCsCqjosJYEPuZ9W8pORheTdwJVi05ccd703"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{api_base_url}/contacts?search={search or ''}"
    response = requests.get(url, headers=headers)

    return response.json()


@tool
def create_contact(first_name: str, email: str, last_name: str = None, phone: str = None):
    """
    Create a contact via the Alfred API using Bearer token authentication.

    Args:
        first_name (str): First name of the contact.
        email (str): Email of the contact.
        last_name (str, optional): Last name of the contact.
        phone (str, optional): Phone number of the contact.

    Returns:
        dict: API response as JSON.
    """
    api_base_url = CONTACTS_URL
    token = "2|uDd2aZH3gFZgNCsCqjosJYEPuZ9W8pORheTdwJVi05ccd703"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{api_base_url}/contacts"
    payload = {
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "phone": phone
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()

@tool
def get_contact_details(contact_id: str):
    """
    Get contact details by ID via the Alfred API using Bearer token authentication.

    Args:
        contact_id (str): The contact ID.

    Returns:
        dict: API response as JSON.
    """
    api_base_url = CONTACTS_URL
    token = "2|uDd2aZH3gFZgNCsCqjosJYEPuZ9W8pORheTdwJVi05ccd703"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{api_base_url}/contacts/{contact_id}"
    response = requests.get(url, headers=headers)

    return response.json()


@tool
def find_contact(first_name: str = None, last_name: str = None, email: str = None):
    """
    Find contact via the Alfred API using Bearer token authentication.

    Args:
        first_name (str, optional): First name of the contact.
        last_name (str, optional): Last name of the contact.
        email (str, optional): Email of the contact.

    Returns:
        dict: API response as JSON.
    """
    api_base_url = CONTACTS_URL
    token = "2|uDd2aZH3gFZgNCsCqjosJYEPuZ9W8pORheTdwJVi05ccd703"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{api_base_url}/contacts/find"
    query_params = {}

    if first_name:
        query_params['first_name'] = first_name
    if last_name:
        query_params['last_name'] = last_name
    if email:
        query_params['email'] = email

    response = requests.get(url, headers=headers, params=query_params)

    return response.json()

@tool
def send_email(subject: str, html: str, to: list, cc: list = None, bcc: list = None):
    """
    Send an email via the Alfred API using Bearer token authentication.

    Args:
        subject (str): Subject of the email.
        html (str): HTML content of the email.
        to (list): List of recipient email addresses (e.g., ["recipient@example.com"]).
        cc (list, optional): List of CC email addresses (e.g., ["cc@example.com"]).
        bcc (list, optional): List of BCC email addresses (e.g., ["bcc@example.com"]).

    Returns:
        dict: API response as JSON.

    Notes:
        The `to`, `cc`, and `bcc` fields must be lists, even for a single recipient.
        Example:
        - "to": ["recipient@example.com"]
        - "cc": ["cc@example.com"]
        - "bcc": ["bcc@example.com"]
    """
    api_base_url = CONTACTS_URL
    token = "2|uDd2aZH3gFZgNCsCqjosJYEPuZ9W8pORheTdwJVi05ccd703"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    url = f"{api_base_url}/send-mail"
    payload = {
        "subject": subject,
        "html": html,
        "to": to,
        "cc": cc,
        "bcc": bcc
    }

    response = requests.post(url, json=payload, headers=headers)

    return response.json()




@tool
def generate_chart(chart_type: str, data: dict, title: str = None) -> dict:
    """
    Calls an API to generate a chart (bar, pie, line, or area) based on provided data.

    Parameters:
    - chart_type: Type of chart ('bar', 'pie', 'line', 'area').
    - data: A dictionary where the keys represent categories, and the values are lists of numbers (arrays).
            Example format:
            {
                "Category1": [10, 20, 30],
                "Category2": [15, 25, 35],
                "Category3": [20, 30, 40]
            }
    - title: Optional title for the chart.

    Sends the user-provided data as the payload and returns the URL of the generated SVG chart or an error message.
    """

    url = CHART_URL

    body_payload = {
        "data": data  # Takes dynamic data from user input
    }

    params = {"chart_type": chart_type}
    if title:
        params["title"] = title

    try:
        response = requests.post(url, json=body_payload, params=params)
        if response.status_code == 200:
            return response.json()  # Assuming the response contains the URL of the SVG chart
        else:
            return {"error": f"Failed to generate chart. Status code: {response.status_code}, Message: {response.text}"}
    except Exception as e:
        return {"error": f"An error occurred: {str(e)}"}