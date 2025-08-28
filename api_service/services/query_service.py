import json
from typing import List, Dict, Any, Optional
from openai import OpenAI
from utils import get_db_connection, Config
from .memory_service import MemoryService
from .graph_service import GraphService
from .citation_service import CitationService, CitationMetadata
from utils.document_db import get_documents_for_chunks, get_citation_for_source
# from .ragas_service import RagasService  # Temporarily disabled due to version conflict

class QueryService:
    def __init__(self):
        self.client = OpenAI(api_key=Config.OPENAI_API_KEY)
        self.memory_service = MemoryService()
        self.graph_service = GraphService()
        self.citation_service = CitationService()
        # self.ragas_service = RagasService()  # Temporarily disabled
    
    def create_embedding(self, text: str) -> List[float]:
        """Create embeddings using OpenAI."""
        response = self.client.embeddings.create(
            input=text,
            model="text-embedding-ada-002"
        )
        return response.data[0].embedding
    
    def vector_search(self, query_embedding: List[float], max_results: int = 5) -> List[Dict[str, Any]]:
        """Perform vector similarity search."""
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                # Convert embedding list to a string representation for pgvector
                embedding_str = '[' + ','.join(map(str, query_embedding)) + ']'
                
                cursor.execute("""
                    SELECT 
                        dc.id, 
                        dc.text_content, 
                        dc.source_metadata,
                        1 - (ce.embedding_vector <=> %s::vector) as similarity
                    FROM 
                        chunk_embeddings ce
                    JOIN 
                        document_chunks dc ON ce.chunk_id = dc.id
                    ORDER BY 
                        ce.embedding_vector <=> %s::vector
                    LIMIT %s
                """, (embedding_str, embedding_str, max_results))
                
                results = cursor.fetchall()
                return results
    
    async def generate_academic_references(self, chunks: List[Dict], style: str = None) -> List[str]:
        """Generate proper academic citations for chunks using DOI-only approach."""
        if style is None:
            style = Config.CITATION_STYLE
            
        references = []
        processed_sources = set()
        
        # Get chunk IDs
        chunk_ids = [chunk['id'] for chunk in chunks]
        
        # Get document metadata for all chunks at once
        documents_by_chunk = get_documents_for_chunks(chunk_ids)
        
        for chunk in chunks:
            chunk_id = chunk['id']
            
            # Get source_metadata for filename
            if isinstance(chunk['source_metadata'], str):
                metadata = json.loads(chunk['source_metadata'])
            else:
                metadata = chunk['source_metadata']
            
            source_filename = metadata.get('source', 'Unknown source')
            
            # Skip if already processed this source
            if source_filename in processed_sources:
                continue
            processed_sources.add(source_filename)
            
            formatted_citation = None
            
            # Only use document table citations that have been fetched via DOI
            if chunk_id in documents_by_chunk:
                doc = documents_by_chunk[chunk_id]
                if doc['citation_fetched'] and doc.get('doi') and doc.get('reference'):
                    # Use pre-fetched DOI-based citation (APA format from doi.org)
                    formatted_citation = doc['reference']
            
            # If no cached citation, perform real-time DOI lookup
            if not formatted_citation:
                # Get DOI from document table or extract from filename
                doi = None
                if chunk_id in documents_by_chunk:
                    doi = documents_by_chunk[chunk_id].get('doi')
                
                if not doi:
                    # Extract DOI from filename using archive pattern
                    async with self.citation_service as citation_service:
                        doi = citation_service.extract_doi_from_filename(source_filename)
                
                # Only proceed if we have a valid DOI
                if doi:
                    async with self.citation_service as citation_service:
                        citation = await citation_service.fetch_citation_from_doi(doi)
                        if citation:
                            formatted_citation = citation
            
            # Add citation to references (only if we have a proper DOI-based citation)
            if formatted_citation and formatted_citation != "Unknown source":
                references.append(formatted_citation)
            else:
                # No fallback - if no DOI or DOI lookup failed, use filename
                references.append(source_filename)
        
        return references
    
    async def generate_answer(self, query: str, chunks: List[Dict], entities: Optional[List[Dict]] = None, 
                       communities: Optional[List[Dict]] = None, use_academic_citations: bool = True) -> tuple[str, List[str]]:
        """Generate answer with references."""
        # Prepare context from chunks
        chunks_context = "\n\n".join([f"Document chunk {i+1}:\n{chunk['text_content']}" 
                                     for i, chunk in enumerate(chunks)])
        
        # Add entity information if available
        entities_context = ""
        if entities:
            entities_context = "\nRelevant entities:\n" + "\n".join([
                f"- {entity['entity']} ({entity['entity_type']}): {entity['relevance']:.2f} relevance" 
                for entity in entities
            ])
        
        # Add community summaries if available
        communities_context = ""
        if communities:
            communities_context = "\nCommunity insights:\n" + "\n".join([
                f"- Community {comm['community_id']}: {comm['summary']}" 
                for comm in communities
            ])
        
        # Full context for the model
        full_context = chunks_context + entities_context + communities_context
        
        # Generate references (academic citations or fallback to filenames)
        if use_academic_citations and Config.ENABLE_ACADEMIC_CITATIONS:
            try:
                references = await self.generate_academic_references(chunks)
            except Exception as e:
                print(f"Error generating academic citations, falling back to filenames: {e}")
                # Fallback to filename references
                references = []
                for chunk in chunks:
                    if isinstance(chunk['source_metadata'], str):
                        metadata = json.loads(chunk['source_metadata'])
                    else:
                        metadata = chunk['source_metadata']
                    source = metadata.get('source', 'Unknown source')
                    if source not in references:
                        references.append(source)
        else:
            # Original filename-based references
            references = []
            for chunk in chunks:
                if isinstance(chunk['source_metadata'], str):
                    metadata = json.loads(chunk['source_metadata'])
                else:
                    metadata = chunk['source_metadata']
                source = metadata.get('source', 'Unknown source')
                if source not in references:
                    references.append(source)
        
        # Generate answer with OpenAI
        prompt = f"""
        Generate a comprehensive answer to the following query based on the provided context. 
        
        Query: {query}
        
        Context:
        {full_context}
        
        Guidelines:
        1. Answer the query using ONLY the information in the provided context.
        2. If the context doesn't contain enough information to fully answer the query, acknowledge the limitations.
        3. Include parenthetical citations when referring to specific information, using the format [chunk1], [chunk2], etc.
        4. Ensure the number of references in your response matches the number of references provided.
        5. Write in a clear, informative, and authoritative style.
        6. Make connections between different pieces of information where relevant.
        7. The answer should be 1-2 paragraphs (3-8 sentences).
        
        References to use (in order):
        {', '.join([f'[chunk{i+1}] {ref}' for i, ref in enumerate(references)])}
        """
        
        response = self.client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a knowledgeable assistant that provides well-researched answers with proper citations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.5
        )
        
        answer = response.choices[0].message.content.strip()
        return answer, references
    
    def generate_simple_answer(self, query: str, context: str) -> str:
        """Generate a simple answer without advanced features."""
        prompt = f"""
        Answer the following question based on the provided context. Keep your answer concise and factual.
        
        Context: {context}
        
        Question: {query}
        
        Answer:"""
        
        response = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that answers questions based on provided context."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        return response.choices[0].message.content.strip()
    
    async def process_query(self, query: str, max_results: int = 5, use_memory: bool = True) -> Dict[str, Any]:
        """Process a user query with optional memory lookup."""
        # Create query embedding
        query_embedding = self.create_embedding(query)
        
        # Check memory if enabled
        if Config.ENABLE_MEMORY and use_memory:
            memory_result = self.memory_service.check_memory(query, query_embedding)
            if memory_result:
                return memory_result
        
        # Perform vector search
        chunks = self.vector_search(query_embedding, max_results)
        
        # Load graph data and enhance results
        entities, communities = self.graph_service.enhance_with_graph(chunks)
        
        # Generate answer (async call)
        answer, references = await self.generate_answer(query, chunks, entities, communities)
        
        # Save to memory
        memory_id = self.memory_service.save_to_memory(
            query, query_embedding, answer, references, chunks, entities, communities
        )
        
        # Format response
        response = {
            "query": query,
            "answer": answer,
            "chunks": [
                {
                    "id": chunk["id"],
                    "text": chunk["text_content"],
                    "source": (json.loads(chunk["source_metadata"]) if isinstance(chunk["source_metadata"], str) 
                             else chunk["source_metadata"]).get("source", "Unknown source"),
                    "similarity": float(chunk["similarity"])
                } for chunk in chunks
            ],
            "entities": entities[:10],  # Top 10 entities
            "communities": communities[:5],  # Top 5 communities
            "references": references,
            "from_memory": False,
            "memory_id": memory_id if memory_id is not None else -1
        }
        
        return response