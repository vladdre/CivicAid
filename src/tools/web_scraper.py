"""
Web Scraper Tool for CivicAid Agent

This tool performs dynamic web scraping ONLY when information is not found
in the vector store or SQL database. It:
1. Checks if information exists in vector_store first
2. If not found, searches for relevant authorized websites
3. Scrapes only from whitelisted, credible sources
4. Adds scraped content to vector_store for future queries
5. Returns the scraped information

Usage:
    This is a tool that will be called by the agent when needed.
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Tuple
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent.parent))

import requests
from bs4 import BeautifulSoup
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_core.documents import Document

load_dotenv()

# Configuration
VECTOR_STORE_DIR = Path(__file__).parent.parent.parent / "data" / "vector_store"
SCRAPED_CONTENT_DIR = Path(__file__).parent.parent.parent / "data" / "scraped_content"

# Chunking parameters (same as ingest_laws.py)
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Whitelist of authorized, credible websites for scraping
AUTHORIZED_DOMAINS = [
    "primariabucuresti.ro",
    "dgaspc.ro",
    "gov.ro",
    "cdep.ro",  # Camera Deputaților
    "senat.ro",  # Senat
    "monitoruloficial.ro",
    "anpc.ro",  # Autoritatea Națională pentru Protecția Consumatorilor
    "cas.ro",  # Casa de Asigurări de Sănătate
    "cnas.ro",  # Casa Națională de Asigurări de Sănătate
    "anofm.gov.ro",  # Agenția Națională pentru Ocuparea Forței de Muncă
    "mmuncii.ro",  # Ministerul Muncii
    "ms.ro",  # Ministerul Sănătății
]

# Base URLs for common searches (can be extended)
AUTHORIZED_BASE_URLS = {
    "primarie": "https://www.primariabucuresti.ro",
    "dgaspc": "https://www.dgaspc.ro",
    "gov": "https://www.gov.ro",
    "monitorul_oficial": "https://www.monitoruloficial.ro",
    # Alternative URLs that actually work
    "gov_home": "https://www.gov.ro",
    "monitorul_home": "https://www.monitoruloficial.ro",
}


def is_authorized_url(url: str) -> bool:
    """
    Check if URL is from an authorized domain.
    
    Args:
        url: URL to check
        
    Returns:
        True if URL is authorized, False otherwise
    """
    for domain in AUTHORIZED_DOMAINS:
        if domain in url.lower():
            return True
    return False


def search_authorized_sites(query: str, max_results: int = 3) -> List[str]:
    """
    Search for relevant URLs from authorized sites based on query.
    
    Note: This is a simplified version. In production, you might want to use:
    - Google Custom Search API (with site: filter)
    - DuckDuckGo API
    - Or a curated list of pages per domain
    
    Args:
        query: Search query
        max_results: Maximum number of URLs to return
        
    Returns:
        List of authorized URLs relevant to the query
    """
    # For now, return base URLs that might contain relevant info
    # In production, implement actual search (e.g., Google Custom Search API)
    urls = []
    
    # Simple keyword matching to suggest relevant sites
    query_lower = query.lower()
    
    # Primărie / Administrație locală
    if any(word in query_lower for word in ["primarie", "primărie", "bucurești", "sector", "administrație", "administratie"]):
        # Încearcă mai întâi site-ul primăriei, apoi fallback la site-uri generale
        urls.append(f"{AUTHORIZED_BASE_URLS['primarie']}/anunturi")
        urls.append(f"{AUTHORIZED_BASE_URLS['primarie']}/servicii")
        # Fallback la site-uri care funcționează
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Asistență socială / DGASPC
    if any(word in query_lower for word in ["asistență", "asistenta", "socială", "sociala", "dgaspc", "alocație", "alocatie", "ajutor social"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['dgaspc']}/noutati")
        urls.append(f"{AUTHORIZED_BASE_URLS['dgaspc']}/servicii")
        # Fallback
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Legislație / Legi / OUG / Monitorul Oficial
    if any(word in query_lower for word in ["lege", "ou", "hotărâre", "hotarare", "monitorul oficial", "monitoruloficial", "legislatie", "legislație"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Accident / Mașină / Rutier / Asigurare auto
    if any(word in query_lower for word in ["accident", "mașină", "masina", "auto", "rutier", "cod rutier", "asigurare auto", "asigurare"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Pensii / Pensie
    if any(word in query_lower for word in ["pensie", "pensii", "pensia", "pensionar"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Sănătate / Medical / Spital
    if any(word in query_lower for word in ["sănătate", "sanatate", "medical", "spital", "casa de asigurări", "cas"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Fiscale / ANAF / Taxe
    if any(word in query_lower for word in ["fiscal", "anaf", "taxe", "impozit", "declarație", "declaratie"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Șomaj / ANOFM / Ocupare
    if any(word in query_lower for word in ["șomaj", "somaj", "anofm", "ocupare", "forță de muncă", "forta de munca"]):
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Dacă nu s-au găsit URL-uri specifice, returnează URL-uri generale care funcționează
    if not urls:
        # Pentru orice query, încercă site-uri generale care funcționează
        urls.append(f"{AUTHORIZED_BASE_URLS['monitorul_oficial']}")
        urls.append(f"{AUTHORIZED_BASE_URLS['gov']}")
    
    # Filter to only authorized domains
    urls = [url for url in urls if is_authorized_url(url)]
    
    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        if url not in seen:
            seen.add(url)
            unique_urls.append(url)
    
    return unique_urls[:max_results]


def scrape_website(url: str) -> Tuple[str, bool]:
    """
    Scrape text content from a website.
    
    Args:
        url: URL to scrape
        
    Returns:
        Tuple of (extracted_text, success)
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script, style, nav, header, footer
        for element in soup(["script", "style", "nav", "header", "footer", "aside"]):
            element.decompose()
        
        # Extract text
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        if len(text) < 100:  # Too short, probably not useful
            return "", False
        
        return text, True
        
    except Exception as e:
        return f"Error scraping {url}: {str(e)}", False


def save_backup(text: str, url: str, output_dir: Path) -> Optional[Path]:
    """
    Save scraped text to backup file.
    
    Args:
        text: Scraped text content
        url: Source URL
        output_dir: Directory to save backup files
        
    Returns:
        Path to saved file or None
    """
    if not text:
        return None
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    date_str = datetime.now().strftime("%Y_%m_%d")
    url_safe = url.replace("https://", "").replace("http://", "").replace("/", "_")[:50]
    filename = f"scraped_{url_safe}_{date_str}.txt"
    filepath = output_dir / filename
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"URL: {url}\n")
            f.write(f"Date: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")
            f.write(text)
        return filepath
    except Exception as e:
        print(f"Warning: Could not save backup: {e}")
        return None


def add_to_vector_store(chunks: List[Document], vector_store_dir: Path) -> bool:
    """
    Add chunks to existing vector store.
    
    Args:
        chunks: List of Document objects
        vector_store_dir: Directory where ChromaDB is persisted
        
    Returns:
        True if successful, False otherwise
    """
    if not chunks:
        return False
    
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return False
        
        embeddings = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=api_key
        )
        
        # Load existing vector store
        if vector_store_dir.exists() and (vector_store_dir / "chroma.sqlite3").exists():
            vector_store = Chroma(
                persist_directory=str(vector_store_dir),
                embedding_function=embeddings,
                collection_name="civicaid_laws"
            )
            vector_store.add_documents(chunks)
            return True
        else:
            # Create new if doesn't exist
            Chroma.from_documents(
                documents=chunks,
                embedding=embeddings,
                persist_directory=str(vector_store_dir),
                collection_name="civicaid_laws"
            )
            return True
    except Exception as e:
        print(f"Error adding to vector store: {e}")
        return False


def scrape_and_index(query: str, vector_store: Optional[Chroma] = None) -> Tuple[str, List[str]]:
    """
    Main function: Scrape authorized websites for query and add to vector store.
    
    This function:
    1. Searches for relevant authorized URLs based on query
    2. Scrapes content from those URLs
    3. Creates chunks with metadata
    4. Adds to vector store
    5. Returns scraped content
    
    Args:
        query: User query to search for
        vector_store: Optional existing vector store instance
        
    Returns:
        Tuple of (formatted_result, list_of_urls_scraped)
    """
    # Step 1: Find relevant authorized URLs
    urls = search_authorized_sites(query, max_results=3)
    
    if not urls:
        return "Nu am găsit site-uri autorizate relevante pentru căutarea ta.", []
    
    # Step 2: Scrape URLs
    scraped_data = []
    successful_urls = []
    
    for url in urls:
        if not is_authorized_url(url):
            continue
        
        text, success = scrape_website(url)
        if success and text:
            scraped_data.append((text, url))
            successful_urls.append(url)
            
            # Save backup
            save_backup(text, url, SCRAPED_CONTENT_DIR)
    
    if not scraped_data:
        return "Nu am putut extrage informații de pe site-urile autorizate.", []
    
    # Step 3: Create documents with metadata
    all_documents = []
    date_str = datetime.now().strftime("%Y-%m-%d")
    
    for text, url in scraped_data:
        doc = Document(
            page_content=text,
            metadata={
                "type": "news",
                "url": url,
                "date": date_str,
                "source": f"web_scraping_{date_str}",
                "query": query  # Store original query for context
            }
        )
        all_documents.append(doc)
    
    # Step 4: Split into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    chunks = text_splitter.split_documents(all_documents)
    
    # Preserve metadata
    for chunk in chunks:
        if "type" not in chunk.metadata:
            chunk.metadata["type"] = "news"
    
    # Step 5: Add to vector store
    success = add_to_vector_store(chunks, VECTOR_STORE_DIR)
    
    if not success:
        return "Am extras informații, dar nu am putut le adăuga în baza de date.", successful_urls
    
    # Step 6: Format result
    result_parts = []
    result_parts.append(f"Am găsit informații pe {len(successful_urls)} site-uri autorizate:\n")
    
    for i, (text, url) in enumerate(scraped_data, 1):
        preview = text[:300].replace("\n", " ")
        result_parts.append(f"{i}. {url}")
        result_parts.append(f"   {preview}...\n")
    
    result_parts.append(f"\nInformațiile au fost adăugate în baza de date pentru viitoarele căutări.")
    
    return "\n".join(result_parts), successful_urls


def web_scraper_tool(query: str, vector_store: Optional[Chroma] = None) -> str:
    """
    Tool function for the agent to use.
    
    This tool should be called ONLY when:
    - Information is not found in vector_store (RAG)
    - Information is not found in SQL database
    - User query requires up-to-date information
    
    Args:
        query: User query
        vector_store: Optional vector store instance (for checking if info exists)
        
    Returns:
        Formatted string with scraped information
    """
    # Check if vector_store is provided and if info might already exist
    if vector_store:
        # Quick check: search in existing store first with relevance threshold
        try:
            # Use similarity_search_with_score to get relevance scores
            results_with_scores = vector_store.similarity_search_with_score(query, k=3)
            
            if results_with_scores:
                # Check relevance threshold
                # Lower score = more similar (ChromaDB uses cosine distance)
                # Score < 0.3 means very relevant, > 0.7 means not relevant
                # We'll use 0.5 as threshold - if best result is below 0.5, it's relevant enough
                best_score = results_with_scores[0][1]
                
                # Also check if the content actually matches the query intent
                best_result = results_with_scores[0][0]
                content_lower = best_result.page_content.lower()
                query_lower = query.lower()
                
                # Extract key words from query (exclude common words)
                common_words = {"ce", "cum", "unde", "când", "care", "este", "sunt", "am", "ai", "are", 
                               "trebuie", "să", "sa", "fac", "faci", "face", "pentru", "despre", "în", "in"}
                query_keywords = [w for w in query_lower.split() if w not in common_words and len(w) > 3]
                
                # Check if at least 2 key words appear in the result
                keywords_found = sum(1 for kw in query_keywords if kw in content_lower)
                relevance_ratio = keywords_found / len(query_keywords) if query_keywords else 0
                
                # If score is low (relevant) AND keywords match, skip scraping
                if best_score < 0.5 and relevance_ratio > 0.3:
                    return f"Informația există deja în baza de date. Nu este necesar scraping."
                # Otherwise, proceed with scraping (info might not be relevant enough)
        except Exception as e:
            # If there's an error checking, proceed with scraping
            pass
    
    # Scrape and index
    result, urls = scrape_and_index(query, vector_store)
    return result

