import os
import openai

from dotenv import load_dotenv
from langchain.docstore.document import Document
from langchain.document_loaders import PyMuPDFLoader
from langchain.embeddings import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from async_redis import AsyncRedis


# TODO ingest azure blob
async def ingest_docs(index: str, input: str):
    print("inside ingest")
    load_dotenv()

    loader = PyMuPDFLoader(input)

    # setup openai
    openai.api_base = os.environ["OPENAI_API_BASE"]
    openai.api_type = os.environ["OPENAI_API_TYPE"]
    openai.api_version = os.environ["OPENAI_API_VERSION"]

    redis_url = os.environ["REDIS_URL"]

    raw_documents = loader.load()
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    documents = text_splitter.split_documents(raw_documents)
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", chunk_size=1)
    rds = await AsyncRedis.afrom_documents(
        documents, embeddings, redis_url=redis_url, index_name=index
    )
    return rds


async def ingest_text(index: str, input: str):
    load_dotenv()

    openai.api_base = os.environ["OPENAI_API_BASE"]
    openai.api_type = os.environ["OPENAI_API_TYPE"]
    openai.api_version = os.environ["OPENAI_API_VERSION"]
    redis_url = os.environ["REDIS_URL"]

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    jd_doc = Document(page_content=input)
    split_doc = text_splitter.split_documents([jd_doc])
    embeddings = OpenAIEmbeddings(model="text-embedding-ada-002", chunk_size=1)
    rds = await AsyncRedis.afrom_documents(
        split_doc, embeddings, redis_url=redis_url, index_name=index
    )

    return rds


if __name__ == "__main__":
    ingest_docs()
