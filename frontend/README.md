# Research Paper Search Interface

A beautiful, modern Vue.js interface for searching and displaying research papers with integrated backend search capabilities.

## Features

- Clean, modern UI with gradient design
- Search functionality with recommended queries
- Card-based layout for displaying papers
- Responsive design for mobile and desktop
- Displays title, authors, organizations, abstract, URL, and metadata
- Real-time search with backend integration
- Semantic search and reranking capabilities

## Usage

### Option 1: Start Frontend and Backend Separately

Start the search backend:
```bash
cd backend
python search_app.py
```

Start the search frontend:
```bash
cd frontend
python3 -m http.server 12311
```