from whoosh.fields import ID, TEXT, Schema
from whoosh.filedb.filestore import RamStorage
from whoosh.qparser import MultifieldParser

SCHEMA = Schema(
    idx=ID(stored=True),
    title=TEXT(field_boost=2.0),
    description=TEXT,
    author=TEXT,
    content=TEXT,  # everything searchable, incl. team number, language, awards, tags
)
FIELDS = ["title", "description", "author", "content"]


def search(query, records):
    """Return the records matching query (Whoosh query syntax), best match first."""
    # ponytail: rebuilds an in-memory index per query; fine for tens of posts per
    # category. Cache the index per category if categories grow into the thousands.
    index = RamStorage().create_index(SCHEMA)
    with index.writer() as writer:
        for i, r in enumerate(records):
            content = [
                r.get("title"),
                r.get("description"),
                r.get("author"),
                r.get("team_number"),
                r.get("language"),
                r.get("awards_won"),
                *r.get("tags", []),
            ]
            writer.add_document(
                idx=str(i),
                title=r.get("title", ""),
                description=r.get("description", ""),
                author=r.get("author", ""),
                content=" ".join(str(c) for c in content if c),
            )

    parsed = MultifieldParser(FIELDS, SCHEMA).parse(query)
    with index.searcher() as searcher:
        return [records[int(hit["idx"])] for hit in searcher.search(parsed, limit=None)]

