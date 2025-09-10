# Starter PGVector/GraphRAG Query System

A containerized application that generates paragraph answers with references based on user queries, powered by PGVector technology.

## Overview
![Real-time Document Ingestion](https://github.com/user-attachments/assets/430d6c1a-0248-4c9e-9db0-33dcf811fbf7)
![Answer 1 (one) Question (no cache)](https://github.com/user-attachments/assets/8967cc37-977f-42f9-98f7-b0a51bc5105b)

This project implements a full-stack RAG (Retrieval-Augmented Generation) system enhanced with graph-based knowledge representation. The system processes documents, builds a knowledge graph of entities and their relationships, and provides comprehensive answers to user queries with proper citations.

### Key Features

- Document ingestion and chunking
- Vector embeddings with OpenAI
- Entity extraction and relationship mapping (fixed)
- Knowledge graph construction (fixed)
- GraphRAG-enhanced retrieval (fixed)
- Paragraph generation with citations
- Interactive web interface
- Query memory with similarity matching
- User feedback and favorites
- Document-grounded conversation threads

## Architecture

The application is fully containerized using Docker and consists of the following components:

### 1. Database (PostgreSQL with pgvector)
- Stores document chunks and their embeddings
- Enables vector similarity search

### 2. Ingestion Service
- Processes documents (PDF, DOCX, TXT)
- Chunks documents and generates embeddings
- Stores data in PostgreSQL

### 3. GraphRAG Processor
- Builds a knowledge graph from document chunks
- Extracts entities and relationships (fixed)
- Generates community summaries
- Outputs graph data for enhanced retrieval

### 4. API Service
- Processes user queries
- Performs vector similarity search
- Enhances retrieval with graph data
- Generates comprehensive answers
- Caches results for similar future queries
- Supports conversation threads and feedback

### 5. Frontend
- Provides a user-friendly interface
- Displays answers with citations
- Shows relevant chunks, entities, and community insights
- Features for feedback, favorites, and conversation threads

## Getting Started

### Prerequisites

- Docker and Docker Compose
- OpenAI API key

### Installation

1. Clone this repository:
   ```
   git clone <repository-url>
   cd containerized-rag-starter-kit 
   ```

2. Create a `.env` file in the root directory with your OpenAI API key:
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

3. Build and start the containers:
   ```
   docker-compose up -d
   ```

4. The application will be available at:
   - Frontend: http://localhost:8080
   - API: http://localhost:8000
   - Database: localhost:5433 (PostgreSQL)

## Development

#### Frontend

1. Go to /frontend

2. Run `$ npm install`

3. Run `$ npm dev`

4. Open browser to http://localhost:5173/

## FAQ

### Database Backup and Restore

The system includes scripts for database backup and restore operations:

```bash
# Create a manual backup (default location: ./backups)
./scripts/backup_db.sh [backup_directory]

# Restore from a backup
./scripts/restore_db.sh path/to/backup_file.sql.gz

# Setup scheduled backups with rotation (keeps last 7 by default)
./scripts/scheduled_backup.sh [backup_directory] [retention_count]
```

For detailed information, see [Database Backup and Restore](docs/backup_restore.md).

## Usage

### Adding Documents

#### Manual Addition
1. Place your documents (PDF, DOCX, TXT, images) in the `data` directory
2. The ingestion service will automatically process them. Run `./scripts/check_ingestion.sh`
   ![to check ingestion progress in CLI](https://github.com/user-attachments/assets/ed2c15f7-f9ec-4ca9-a9cd-379400adb173)

4. The GraphRAG processor will build the knowledge graph

> **Note:** The system supports scanned PDFs and images through OCR processing

#### Bulk Import from Zotero
The project includes two scripts for importing documents in bulk from Zotero storage:

##### Basic Import
1. Run the basic import script:
   ```
   ./scripts/import_documents.sh /home/mu/Zotero/storage
   ```
   
2. The script will:
   - Find all PDF, DOCX, and TXT files in the Zotero storage directory and its subdirectories
   - Copy them to the `data` directory (skipping any duplicates by filename)
   - Report how many new documents were added

##### Advanced Import with Metadata
For a more sophisticated import that preserves folder structure information:

1. Run the advanced import script:
   ```
   ./scripts/import_with_metadata.py /home/mu/Zotero/storage
   ```
   
2. The advanced script offers additional features:
   - Content-based deduplication (using file hashes)
   - Preserves source folder information in filenames
   - Creates a JSON metadata file with original paths and other information
   - Provides more options (run with `--help` to see all options)

   Additional options:
   ```
   # Preserve directory structure in target
   ./scripts/import_with_metadata.py --preserve-structure
   
   # Specify a custom target directory
   ./scripts/import_with_metadata.py --target-dir ./custom_data_dir
   ```

##### Import with OCR Support
For handling scanned documents and images:

1. Run the OCR-enabled import script:
   ```
   ./scripts/import_with_ocr.py /home/mu/Zotero/storage
   ```
   
2. This script provides all the features of the metadata script plus:
   - Automatic detection of scanned PDFs and images
   - OCR processing to make non-searchable documents searchable
   - Parallel processing for faster imports
   - Integration with the OCR service

   Additional options:
   ```
   # Force OCR processing for all documents
   ./scripts/import_with_ocr.py --force-ocr
   
   # Disable OCR processing
   ./scripts/import_with_ocr.py --no-ocr
   
   # Adjust processing threads
   ./scripts/import_with_ocr.py --threads 8
   ```

3. The ingestion service will automatically process the imported documents

> **OCR Note:** The system includes two OCR solutions:
> - Built-in OCR in the ingestion service for direct processing
> - Dedicated OCR service for more advanced preprocessing during import

### Querying

1. Open the frontend at http://localhost:8080
2. Enter your query in the search box
3. View the generated answer with citations
4. Explore the relevant chunks
## Technical Details

### Vector Storage and Search

The system uses PostgreSQL with the pgvector extension to store and search vector embeddings, enabling efficient similarity search for relevant document chunks.

### Knowledge Graph Construction

The GraphRAG processor extracts entities from document chunks using spaCy and builds a knowledge graph representing relationships between entities and chunks.

### Query Processing

When a user submits a query:

1. The query is embedded using OpenAI
2. The system checks memory for similar previous queries
3. If not found in memory, relevant chunks are retrieved using vector search
4. The knowledge graph is queried for related entities and communities
5. A comprehensive answer is generated with citations
6. The result is stored in memory for future similar queries

### Memory and Conversation Features

The system includes several enhanced features:

1. **Query Memory**: The system remembers previous queries and can instantly retrieve answers for similar questions without regenerating them.

2. **User Feedback**: Users can rate answers on a 5-star scale and provide text feedback.

3. **Favorites**: Users can bookmark particularly useful answers for quick reference later.

4. **Conversation Threads**: Users can start a conversation thread from any query, enabling follow-up questions with document-grounded responses.

5. **Enhanced Retrieval**: Conversation threads can optionally include document retrieval to ground responses in the knowledge base.

## Development

### Project Structure

```
writehere-graphrag/
├── data/                  # Document storage directory
├── db/                    # Database configuration
├── docs/                  # Documentation files
├── ingestion_service/     # Document processing service
├── graphrag_processor/    # Knowledge graph generator
├── api_service/           # Query processing API
├── frontend/              # Vue.js web interface
├── scripts/               # Utility scripts for backup, import, etc.
└── docker-compose.yml     # Container orchestration
```

### Customization

- Modify the chunking parameters in `ingestion_service/app.py`
- Adjust the graph processing interval in `graphrag_processor/app.py`
- Change the UI appearance in `frontend/src/assets/main.css`

## ILRI deployment

This setup runs only the database, ingestion service, API service, and GROBID. The frontend runs outside Docker with its own NGINX and optional systemd unit.

### Services (ILRI compose)
- **Database**: `db-ilri` (PostgreSQL + pgvector) on port 5434
- **GROBID**: `grobid-ilri` on port 8070
- **API**: `api-service-ilri` on port 8001
- **Ingestion**: `ingestion-service-ilri` on port 5051
- Frontend is not run in Docker for ILRI; run it outside as described below

Compose file: `docker-compose.ilri.yml`

### Start ILRI stack (no frontend in Docker)
```bash
# Expects OPENAI_API_KEY in environment (and optionally ANTHROPIC_API_KEY)
export OPENAI_API_KEY=...  # required
export ANTHROPIC_API_KEY=...  # optional

./run-ilri-instance.sh

# Check status / logs
docker compose -f docker-compose.ilri.yml ps
docker compose -f docker-compose.ilri.yml logs -f
```

### GROBID integration (required for ingestion)
- Ingestion uses `grobid-client` with config mounted at `/app/grobid_config.json`
- ILRI-specific config points to the in-network GROBID service: `ingestion_service/grobid_config.ilri.json`
- The ILRI compose mounts this file and ensures `ingestion-service-ilri` depends on `grobid-ilri`

### Frontend outside Docker
You have two options:

1) Development (Vite dev server)
- Run:
  ```bash
  cd frontend
  npm install
  npm dev  # defaults to http://localhost:5173
  ```
- Update NGINX reverse proxy to route the site to Vite and API to the ILRI API:
  - File: `deployment/nginx/containerized-rag`
    - Change frontend proxy target to `http://localhost:5173`
    - Change API proxy target to `http://localhost:8001/`

2) Production (build and serve via system NGINX)
- Build static assets:
  ```bash
  cd frontend
  npm install
  npm build  # outputs to ./dist
  ```
- Configure your NGINX server block to serve `frontend/dist` as root and proxy `/api/` to `http://localhost:8001/`.
  Example:
  ```nginx
  server {
    listen 80;
    server_name ilri.example.org;

    root /home/muhia/src/containerized-rag-starter-kit/frontend/dist;
    index index.html;

    location /api/ {
      proxy_pass http://localhost:8001/;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_read_timeout 300s;
    }

    location / {
      try_files $uri $uri/ /index.html;
    }
  }
  ```
- Optionally add a systemd unit for NGINX or your deployment routine per your environment.

### ILRI branding (frontend)
Update the name and branding in the frontend:
- Change page title in `frontend/index.html`:
  ```startLine:endLine:frontend/index.html
  <title>AI Search</title>
  ```
  to e.g. `ILRI AI Search`.
- Change nav brand in `frontend/src/App.vue`:
  ```startLine:endLine:frontend/src/App.vue
  <h1>AI Search</h1>
  ```
  to e.g. `ILRI AI Search`.
- Add ILRI logo and colors in `frontend/src/assets/main.css` or component styles as desired.

### Dev proxy (optional)
If using Vite dev server, point `/api` proxy to the ILRI API port:
- File: `frontend/vite.config.js`
  ```js
  export default defineConfig({
    server: {
      proxy: {
        '/api': { target: 'http://localhost:8001', changeOrigin: true, rewrite: p => p.replace(/^\/api/, '') }
      }
    }
  })
  ```

### Endpoints
- Frontend: via external NGINX (per config above)
- API: `http://localhost:8001`
- Health: `http://localhost:8001/health`
- GROBID UI: `http://localhost:8070`

## License

[MIT License](LICENSE)
