"""
Data Ingestion Pipeline for CivicAid RAG System

This script implements the ETL pipeline for ingesting PDF legal documents:
1. Load: Scans data/raw_laws folder and loads PDFs using PyPDFLoader
2. Split: Chunks documents using RecursiveCharacterTextSplitter
3. Embed: Creates embeddings using OpenAIEmbeddings
4. Store: Saves vectors to ChromaDB at data/vector_store

Usage:
    python scripts/ingest_laws.py
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma

# Load environment variables
load_dotenv()

# Configuration
RAW_LAWS_DIR = Path(__file__).parent.parent / "data" / "raw_laws"
VECTOR_STORE_DIR = Path(__file__).parent.parent / "data" / "vector_store"

# Chunking parameters (as per technical specs)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200


def load_pdfs(raw_laws_dir: Path) -> list:
    """
    Load all PDF files from the raw_laws directory.
    
    Args:
        raw_laws_dir: Path to directory containing PDF files
        
    Returns:
        List of loaded Document objects
    """
    documents = []
    
    if not raw_laws_dir.exists():
        print(f"⚠️  Directory {raw_laws_dir} does not exist. Creating it...")
        raw_laws_dir.mkdir(parents=True, exist_ok=True)
        print(f"📁 Please add PDF files to {raw_laws_dir} and run the script again.")
        return documents
    
    pdf_files = list(raw_laws_dir.glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {raw_laws_dir}")
        print(f"📁 Please add PDF files to {raw_laws_dir} and run the script again.")
        return documents
    
    print(f"📚 Found {len(pdf_files)} PDF file(s). Loading...")
    
    for pdf_path in pdf_files:
        try:
            print(f"  📄 Loading: {pdf_path.name}")
            loader = PyPDFLoader(str(pdf_path))
            docs = loader.load()
            
            # Add metadata about source file
            for doc in docs:
                doc.metadata["source"] = pdf_path.name
                doc.metadata["file_path"] = str(pdf_path)
            
            documents.extend(docs)
            print(f"    ✓ Loaded {len(docs)} pages from {pdf_path.name}")
            
        except Exception as e:
            print(f"    ✗ Error loading {pdf_path.name}: {str(e)}")
            continue
    
    return documents


def split_documents(documents: list, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> list:
    """
    Split documents into chunks using RecursiveCharacterTextSplitter.
    
    Args:
        documents: List of Document objects
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks to preserve context
        
    Returns:
        List of chunked Document objects
    """
    if not documents:
        return []
    
    print(f"\n✂️  Splitting documents into chunks (size={chunk_size}, overlap={chunk_overlap})...")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]  # Priority order for splitting
    )
    
    chunks = text_splitter.split_documents(documents)
    print(f"  ✓ Created {len(chunks)} chunks from {len(documents)} documents")
    
    return chunks


def create_vector_store(chunks: list, vector_store_dir: Path) -> Chroma:
    """
    Create embeddings and store them in ChromaDB.
    
    Args:
        chunks: List of chunked Document objects
        vector_store_dir: Directory where ChromaDB will be persisted
        
    Returns:
        Chroma vector store instance
    """
    if not chunks:
        print("⚠️  No chunks to embed. Skipping vector store creation.")
        return None
    
    # Check for OpenAI API key
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            "Please set it in your .env file."
        )
    
    print(f"\n🔢 Creating embeddings using OpenAI...")
    
    # Initialize embeddings
    embeddings = OpenAIEmbeddings(
        model="text-embedding-3-small",  # Cost-effective embedding model
        openai_api_key=api_key
    )
    
    print(f"💾 Storing vectors in ChromaDB at {vector_store_dir}...")
    
    # Create or load vector store
    # If vector_store_dir exists, it will load existing data
    # Otherwise, it will create a new store
    # Note: Chroma automatically persists when persist_directory is specified
    vector_store = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=str(vector_store_dir),
        collection_name="civicaid_laws"  # Named collection for clarity
    )
    
    print(f"  ✓ Vector store created/updated successfully!")
    print(f"  ✓ Total documents indexed: {len(chunks)}")
    
    return vector_store


def main():
    """
    Main ETL pipeline execution.
    """
    print("=" * 60)
    print("🚀 CivicAid - Legal Documents Ingestion Pipeline")
    print("=" * 60)
    
    # Step 1: Load PDFs
    documents = load_pdfs(RAW_LAWS_DIR)
    
    if not documents:
        print("\n❌ No documents to process. Exiting.")
        return
    
    # Step 2: Split into chunks
    chunks = split_documents(documents)
    
    if not chunks:
        print("\n❌ No chunks created. Exiting.")
        return
    
    # Step 3: Create embeddings and store in ChromaDB
    try:
        vector_store = create_vector_store(chunks, VECTOR_STORE_DIR)
        
        if vector_store:
            print("\n" + "=" * 60)
            print("✅ Ingestion pipeline completed successfully!")
            print("=" * 60)
            print(f"\n📊 Summary:")
            print(f"   • PDF files processed: {len(set(doc.metadata.get('source', 'unknown') for doc in documents))}")
            print(f"   • Total pages: {len(documents)}")
            print(f"   • Total chunks: {len(chunks)}")
            print(f"   • Vector store location: {VECTOR_STORE_DIR}")
            print(f"\n💡 You can now use the vector store in your RAG tool!")
            
    except Exception as e:
        print(f"\n❌ Error during vector store creation: {str(e)}")
        print(f"   Make sure OPENAI_API_KEY is set in your .env file.")
        sys.exit(1)


if __name__ == "__main__":
    main()

