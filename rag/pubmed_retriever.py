"""
PubMedRetriever — fetches real citations from NCBI Entrez API.
Completely free. No API key required for basic use.
"""
from __future__ import annotations
import requests
import xml.etree.ElementTree as ET
from typing import List, Dict

NCBI_SEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_FETCH  = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
NCBI_SUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def search_pubmed(query: str, max_results: int = 5) -> List[Dict]:
    """Search PubMed and return article summaries."""
    try:
        # Step 1: search for PMIDs
        search_resp = requests.get(NCBI_SEARCH, params={
            "db": "pubmed",
            "term": query,
            "retmax": max_results,
            "retmode": "json",
            "sort": "relevance",
        }, timeout=10)
        
        if search_resp.status_code != 200:
            return []
        
        pmids = search_resp.json().get("esearchresult", {}).get("idlist", [])
        if not pmids:
            return []
        
        # Step 2: fetch summaries
        summary_resp = requests.get(NCBI_SUMMARY, params={
            "db": "pubmed",
            "id": ",".join(pmids),
            "retmode": "json",
        }, timeout=10)
        
        if summary_resp.status_code != 200:
            return []
        
        result_data = summary_resp.json().get("result", {})
        citations = []
        
        for pmid in pmids:
            article = result_data.get(pmid, {})
            if not article:
                continue
            
            authors = article.get("authors", [])
            author_str = ""
            if authors:
                last_names = [a.get("name", "") for a in authors[:3]]
                author_str = ", ".join(last_names)
                if len(authors) > 3:
                    author_str += " et al."
            
            citations.append({
                "pmid": pmid,
                "title": article.get("title", "").rstrip("."),
                "authors": author_str,
                "journal": article.get("source", ""),
                "year": article.get("pubdate", "")[:4],
                "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            })
        
        return citations
    
    except Exception as e:
        return []


def build_rag_query(diagnoses: list, patient_input: str) -> str:
    """Build an optimised PubMed query from diagnoses."""
    if not diagnoses:
        return patient_input[:100]
    top = diagnoses[0].get("name", "")
    icd = diagnoses[0].get("icd10", "")
    return f"{top} treatment guidelines evidence"
