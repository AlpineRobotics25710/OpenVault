# OpenVault Search System - Whoosh Integration

## Overview

The OpenVault search system has been upgraded from a basic TF-IDF implementation to use **Whoosh**, a powerful pure-Python search library. This provides better search capabilities, query parsing, and is optimized for serverless environments like Vercel.

## Key Features

### 🔍 Advanced Search Capabilities
- **Multi-field search**: Searches across title, description, author, and content fields
- **Field boosting**: Title matches are weighted higher than other fields
- **Query parsing**: Supports advanced search syntax (AND, OR, quotes for phrases, etc.)
- **Fuzzy matching**: Better handling of typos and similar terms

### 🚀 Serverless Compatibility
- **In-memory indexing**: Uses RAM storage instead of disk files (perfect for Vercel)
- **Dynamic index rebuilding**: Automatically rebuilds index when content changes
- **No persistent files**: No need to worry about filesystem write permissions

### 🔄 Automatic Content Updates
- **Change detection**: Automatically detects when records have changed
- **Fresh data fetching**: Always fetches latest data from GitHub for searches
- **Hash-based caching**: Only rebuilds index when actual content changes

## How It Works

### Schema Design
The search index includes these fields:
- **title** (TEXT, boosted): Main title field with higher search weight
- **description** (TEXT): Detailed descriptions
- **author** (TEXT): Author names
- **content** (TEXT): Combined searchable content
- **team_number**, **years_used** (KEYWORD): Structured data
- **language**, **awards_won**, **used_in_comp** (KEYWORD/TEXT): Category-specific fields

### Search Process
1. **Index Building**: Creates in-memory index from current records
2. **Change Detection**: Uses MD5 hash to detect if records have changed
3. **Query Parsing**: Parses user queries using Whoosh's MultifieldParser
4. **Result Ranking**: Returns results ranked by Whoosh's BM25F scoring algorithm

## API Endpoints

### Search API
```
POST /api/search
{
  "query": "search terms here"
}
```
- Automatically fetches fresh data from GitHub
- Rebuilds index if content has changed
- Returns HTML template with filtered results

### Refresh Index API
```
POST /api/refresh-search-index
```
- Manually refreshes the search index
- Useful after new content is added
- Forces complete index rebuild

## Search Query Examples

### Basic Search
```
robot design
```
Searches for documents containing "robot" OR "design"

### Phrase Search
```
"intake mechanism"
```
Searches for the exact phrase "intake mechanism"

### Field-Specific Search
```
title:drivetrain
```
Searches only in the title field for "drivetrain"

### Advanced Queries
```
(robot OR drivetrain) AND author:teamname
```
Complex boolean queries with field specifications

## Benefits Over Previous System

### Performance
- **Faster searches**: Optimized indexing and BM25F scoring
- **Better relevance**: More sophisticated ranking algorithm
- **Efficient memory usage**: Only rebuilds when necessary

### Serverless Compatibility
- **No disk I/O**: Works perfectly on Vercel's read-only filesystem
- **Stateless**: Each request can rebuild index independently
- **Scalable**: Memory usage scales with content size

### Search Quality
- **Relevance ranking**: Better results ordering
- **Query flexibility**: Supports complex search syntax
- **Typo tolerance**: Better handling of misspelled terms

## Technical Implementation

### Key Classes
- **WhooshSearchEngine**: Main search engine class
- **Schema**: Defines searchable fields and their types
- **MultifieldParser**: Handles complex query parsing

### Memory Management
- Uses `RamStorage` for in-memory indexing
- Automatic garbage collection when index is rebuilt
- Hash-based change detection to minimize rebuilds

### Error Handling
- Graceful fallback to showing all records on search errors
- Multiple parser fallbacks for malformed queries
- Comprehensive exception handling throughout

## Content Updates

### Automatic Updates
The system automatically handles content updates in two ways:

1. **Fresh Data Fetching**: Every search fetches the latest data from GitHub
2. **Change Detection**: Compares content hash to detect updates
3. **Index Rebuilding**: Rebuilds index only when content actually changes

### Manual Refresh
You can manually refresh the search index using:
```javascript
fetch('/api/refresh-search-index', { method: 'POST' })
```

This is particularly useful after:
- Adding new content through the contribute page
- Making changes to existing content
- When you want to ensure the search index is completely up-to-date

## Deployment Notes

### Vercel Compatibility
- ✅ No file system writes required
- ✅ Pure Python implementation
- ✅ Memory-efficient indexing
- ✅ Stateless operation

### Dependencies
Added to `requirements.txt`:
```
Whoosh==2.7.4
```

### Environment Variables
No additional environment variables required. The system works out-of-the-box with the existing GitHub API integration.
