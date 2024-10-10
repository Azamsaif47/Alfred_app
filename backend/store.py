import os
import uuid
import json
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.schema import Document
import openai
from langchain.text_splitter import CharacterTextSplitter
import docx2txt
from PyPDF2 import PdfReader
import psycopg2
from Crypto.Cipher import AES

load_dotenv()


database_url = os.getenv('DATABASE_URL')
openai.api_key = os.getenv('OPENAI_API_KEY')


def connect_db():
    try:
        conn = psycopg2.connect(database_url)

        return conn
    except Exception as e:
        print(f"Error connecting to the database: {e}")
        return None



def load_and_split_documents(doc_folder):
    all_documents = []

    for root, dirs, files in os.walk(doc_folder):
        for file in files:
            file_path = os.path.join(root, file)

            if file.lower().endswith('.pdf'):
                try:
                    with open(file_path, 'rb') as f:
                        reader = PdfReader(f)
                        if reader.is_encrypted:
                            print(f"PDF {file_path} is encrypted, attempting decryption...")
                            try:
                                reader.decrypt("")  # Decrypt without a password
                            except Exception as decryption_error:
                                print(f"Failed to decrypt {file_path}: {decryption_error}")
                                continue

                            pages = [page.extract_text() for page in reader.pages]
                            for page_content in pages:
                                all_documents.append(
                                    Document(page_content=page_content, metadata={"source": file_path}))
                        else:
                            loader = PyPDFLoader(file_path, extract_images=False)
                            pages = loader.load()

                            for page in pages:
                                all_documents.append(
                                    Document(page_content=page.page_content, metadata={"source": file_path}))

                    print(f"Successfully processed PDF: {file_path}.")
                except Exception as e:
                    print(f"Error processing PDF {file_path}: {e}")


            elif file.lower().endswith('.docx'):
                try:
                    text = docx2txt.process(file_path)
                    all_documents.append(Document(page_content=text, metadata={"source": file_path}))
                    print(f"Successfully processed DOCX: {file_path}.")
                except Exception as e:
                    print(f"Error processing DOCX {file_path}: {e}")

    return all_documents



doc_folder = "path_to_your_docs"


folder_name = input("Enter the name for the folder to save the vector store: ")
folder_path = os.path.join("Path_for_vectorstore", folder_name)


os.makedirs(folder_path, exist_ok=True)


loaded_documents = load_and_split_documents(doc_folder)

text_splitter = CharacterTextSplitter(
    separator="\n",
    chunk_size=1000,
    chunk_overlap=150,
    length_function=len
)


docs = text_splitter.split_documents(loaded_documents)

embeddings = OpenAIEmbeddings()


vectordb = FAISS.from_documents(
    documents=docs,
    embedding=embeddings
)


index_name = "faiss.index"
vectordb.save_local(folder_path, index_name)

def accumulate_vectors(docs, folder_name):
    """Accumulate the vector data from documents."""
    vector_data=[]
    for doc in docs:

        vector_id = str(uuid.uuid4())
        file_id = str(uuid.uuid4())

        metadata = doc.metadata
        metadata_str = json.dumps(metadata)

        vector_data.append((vector_id, file_id, folder_name, metadata_str))
        break

    return vector_data


def insert_vectors_batch(conn, vector_data):
    """Insert vector data into PostgreSQL database in a single batch."""
    print(f"this is the vector data :{vector_data}")
    with conn.cursor() as cursor:
        try:
            insert_query = """
                INSERT INTO vector (vector_id, file_id, name, metadata)
                VALUES (%s, %s, %s, %s)
            """
            cursor.executemany(insert_query, vector_data)
            print(f"Inserted {len(vector_data)} vectors into database.")
        except Exception as e:
            print(f"Error during batch insertion: {e}")
            conn.rollback()


conn = connect_db()

if conn:

    vector_data = accumulate_vectors(docs, folder_name)


    if vector_data:
        insert_vectors_batch(conn, vector_data)
        conn.commit()
        print(f"Vectors saved successfully in the PostgreSQL database.")

    conn.close()

print(f"Vector store saved successfully in '{folder_path}' with index file name '{index_name}'.")
