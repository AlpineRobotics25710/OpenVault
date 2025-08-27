import os
import tempfile
import hashlib
import json
from whoosh.index import create_in, open_dir, exists_in
from whoosh.fields import Schema, TEXT, ID, KEYWORD, STORED
from whoosh.qparser import QueryParser, MultifieldParser
from whoosh import writing
from whoosh.analysis import StandardAnalyzer
from whoosh.filedb.filestore import RamStorage


class WhooshSearchEngine:
    def __init__(self, use_memory=True):
        self.use_memory = use_memory  # Use in-memory storage for serverless
        self.schema = self._create_schema()
        self.index = None
        self.storage = None
        self._records_hash = None  # Track if records have changed

    def _create_schema(self):
        """Create the search schema with appropriate field types"""
        return Schema(
            # Unique identifier for each document
            uuid=ID(unique=True, stored=True),
            # Main searchable text fields with higher boost for title
            title=TEXT(stored=True, field_boost=2.0),
            description=TEXT(stored=True),
            author=TEXT(stored=True),
            # Structured data fields
            team_number=KEYWORD(stored=True),
            years_used=KEYWORD(stored=True),
            timestamp=ID(stored=True),
            # Category-specific fields
            language=KEYWORD(stored=True),  # for code
            awards_won=TEXT(stored=True),  # for portfolios
            used_in_comp=KEYWORD(stored=True),  # for code and cad
            # URLs and file paths
            preview_image_url=STORED,
            download_url=STORED,
            onshape_link=STORED,
            # Combined searchable content for full-text search
            content=TEXT(analyzer=StandardAnalyzer()),
        )

    def _get_records_hash(self, records):
        """Generate a hash of the records to detect changes"""
        if not records:
            return None

        # Create a hash based on the records content
        records_str = json.dumps(records, sort_keys=True, default=str)
        return hashlib.md5(records_str.encode()).hexdigest()

    def _needs_rebuild(self, records):
        """Check if the index needs to be rebuilt"""
        current_hash = self._get_records_hash(records)

        # Rebuild if no index exists, no hash stored, or hash changed
        if (
            self.index is None
            or self._records_hash is None
            or self._records_hash != current_hash
        ):
            return True, current_hash

        return False, current_hash

    def build_index(self, records):
        """Build or rebuild the Whoosh index from records"""
        if not records:
            return None

        # Check if we need to rebuild the index
        needs_rebuild, current_hash = self._needs_rebuild(records)

        if not needs_rebuild and self.index is not None:
            return self.index

        try:
            # Use in-memory storage for serverless environments
            if self.use_memory:
                self.storage = RamStorage()
                self.index = self.storage.create_index(self.schema)
            else:
                # Fallback to temporary directory for local development
                temp_dir = tempfile.mkdtemp()
                self.index = create_in(temp_dir, self.schema)

            writer = self.index.writer()

            for record in records:
                # Combine all searchable text content
                content_parts = []
                content_parts.append(record.get("title", ""))
                content_parts.append(record.get("description", ""))
                content_parts.append(record.get("author", ""))

                # Add category-specific content
                if "language" in record:
                    content_parts.append(record["language"])
                if "awards_won" in record:
                    content_parts.append(record["awards_won"])

                combined_content = " ".join(str(part) for part in content_parts if part)

                # Add document to index
                writer.add_document(
                    uuid=record["uuid"],
                    title=record.get("title", ""),
                    description=record.get("description", ""),
                    author=record.get("author", ""),
                    team_number=str(record.get("team_number", "")),
                    years_used=" ".join(map(str, record.get("years_used", []))),
                    timestamp=record.get("timestamp", ""),
                    language=record.get("language", ""),
                    awards_won=record.get("awards_won", ""),
                    used_in_comp=str(record.get("used_in_comp", "")),
                    preview_image_url=record.get("preview_image_url", ""),
                    download_url=record.get("download_url", ""),
                    onshape_link=record.get("onshape_link", ""),
                    content=combined_content,
                )

            writer.commit()
            self._records_hash = current_hash
            return self.index

        except Exception as e:
            print(f"Error building search index: {e}")
            # Reset state on error
            self.index = None
            self._records_hash = None
            return None

    def search(self, query_string, records, limit=None):
        """
        Search the index using Whoosh
        Returns (similarities, ranked_indices) for compatibility with existing code
        """
        # Always rebuild index if records have changed (important for dynamic content)
        index = self.build_index(records)

        if not index:
            # Fallback: return all records if index creation fails
            similarities = [1.0] * len(records)
            ranked_indices = list(range(len(records)))
            return similarities, ranked_indices

        if not query_string.strip():
            # Return all results if empty query
            similarities = [1.0] * len(records)
            ranked_indices = list(range(len(records)))
            return similarities, ranked_indices

        # Create a multi-field parser that searches across multiple fields
        parser = MultifieldParser(
            ["title", "description", "author", "content"], index.schema
        )

        try:
            query = parser.parse(query_string)
        except:
            # Fallback to simple content search if parsing fails
            parser = QueryParser("content", index.schema)
            try:
                query = parser.parse(query_string)
            except:
                # If all parsing fails, return all records
                similarities = [1.0] * len(records)
                ranked_indices = list(range(len(records)))
                return similarities, ranked_indices

        similarities = []
        ranked_indices = []
        uuid_to_index = {record["uuid"]: i for i, record in enumerate(records)}

        try:
            with index.searcher() as searcher:
                results = searcher.search(query, limit=limit)

                # Convert Whoosh results back to original format
                for hit in results:
                    uuid = hit["uuid"]
                    if uuid in uuid_to_index:
                        original_index = uuid_to_index[uuid]
                        ranked_indices.append(original_index)
                        # Use Whoosh's score as similarity
                        similarities.append(hit.score if hasattr(hit, "score") else 1.0)

            # Add remaining records with 0 similarity
            remaining_indices = [
                i for i in range(len(records)) if i not in ranked_indices
            ]
            ranked_indices.extend(remaining_indices)
            similarities.extend([0.0] * len(remaining_indices))

        except Exception as e:
            print(f"Search execution error: {e}")
            # Fallback: return all records on search error
            similarities = [1.0] * len(records)
            ranked_indices = list(range(len(records)))

        return similarities, ranked_indices

    def get_suggestions(self, query_string, records, max_suggestions=5):
        """Get search suggestions using Whoosh's spelling correction"""
        index = self.build_index(records)
        if not index:
            return []

        try:
            with index.searcher() as searcher:
                corrector = searcher.corrector("content")
                suggestions = []

                words = query_string.lower().split()
                for word in words:
                    suggested = corrector.suggest(word, limit=3)
                    if suggested and suggested[0] != word:
                        suggestions.extend(suggested[:max_suggestions])

                return list(set(suggestions))[:max_suggestions]
        except Exception as e:
            print(f"Suggestion error: {e}")
            return []


# Global search engine instance configured for serverless
# For local development, you can change use_memory=False to use disk-based indexing
_search_engine = WhooshSearchEngine(use_memory=True)


def build_index(records):
    """
    Legacy function for compatibility with existing code
    Returns (index, None, None, None) to match expected return format
    """
    index = _search_engine.build_index(records)
    return index, None, None, None


def search(
    query,
    records_or_legacy_param=None,
    legacy_param2=None,
    legacy_param3=None,
    records=None,
):
    """
    Legacy function for compatibility with existing code
    Can be called as:
    - search(query, records=records) - new way
    - search(query, idf, vocab, tfidf_matrix) - old way (will need records from session)
    """
    if records is None:
        # This means we're being called the old way
        # We need to get records from somewhere - this should be handled by the caller
        raise ValueError("Records must be provided for Whoosh search")

    try:
        similarities, ranked_indices = _search_engine.search(query, records)
        return similarities, ranked_indices
    except Exception as e:
        print(f"Search error in legacy wrapper: {e}")
        # Fallback: return all records with equal similarity
        similarities = [1.0] * len(records)
        ranked_indices = list(range(len(records)))
        return similarities, ranked_indices


def get_search_suggestions(query, records):
    """Get search suggestions for the given query"""
    try:
        return _search_engine.get_suggestions(query, records)
    except Exception as e:
        print(f"Suggestions error: {e}")
        return []


def force_index_rebuild():
    """Force the search index to be rebuilt on next search"""
    global _search_engine
    _search_engine._records_hash = None
    _search_engine.index = None


def get_search_stats(records):
    """Get statistics about the search index"""
    try:
        index = _search_engine.build_index(records)
        if not index:
            return {"error": "Could not build index"}

        with index.searcher() as searcher:
            return {
                "total_documents": searcher.doc_count_all(),
                "indexed_fields": list(index.schema.names()),
                "index_type": (
                    "in-memory" if _search_engine.use_memory else "disk-based"
                ),
            }
    except Exception as e:
        return {"error": str(e)}
