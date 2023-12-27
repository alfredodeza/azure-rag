import os
import openai
from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import AzureSearch


app = FastAPI()

openai.api_base = os.getenv("OPENAI_API_BASE")  # Your Azure OpenAI resource's endpoint value.
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.api_type = "azure"
openai.api_version = "2023-05-15" 

embeddings = OpenAIEmbeddings(deployment="demo-embedding", chunk_size=1)

# Connect to Azure Cognitive Search
acs = AzureSearch(azure_search_endpoint=os.getenv('SEARCH_SERVICE_NAME'),
                 azure_search_key=os.getenv('SEARCH_API_KEY'),
                 index_name=os.getenv('SEARCH_INDEX_NAME'),
                 embedding_function=embeddings.embed_query)

class Body(BaseModel):
    query: str


@app.get('/')
def root():
    return RedirectResponse(url='/docs', status_code=301)


@app.post('/ask')
def ask(body: Body):
    """
    Use the query parameter to interact with the Azure OpenAI Service
    using the Azure Cognitive Search API for Retrieval Augmented Generation.
    """
    search_result = search(body.query)
    chat_bot_response = assistant(body.query, search_result)
    return {'response': chat_bot_response}



def search(query):
    """
    Send the query to Azure Cognitive Search and return the top result
    """
    docs = acs.similarity_search_with_relevance_scores(
        query=query,
        k=5,
    )
    result = docs[0][0].page_content
    print(result)
    return result


def assistant(query, context):
    messages=[
        # Set the system characteristics for this chat bot
        {"role": "system", "content": "Asisstant is a chatbot that helps you find the best wine for your taste."},

        # Set the query so that the chatbot can respond to it
        {"role": "user", "content": query},

        # Add the context from the vector search results so that the chatbot can use
        # it as part of the response for an augmented context
        {"role": "assistant", "content": context}
    ]

    response = openai.ChatCompletion.create(
        engine="demo-alfredo",
        messages=messages,
    )
    return response['choices'][0]['message']['content']