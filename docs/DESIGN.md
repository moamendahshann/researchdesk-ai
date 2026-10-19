# Design decisions

## Evidence first

Each chunk retains its document ID and physical PDF page number. The UI links directly to that page and displays the full retrieved chunk. PDF viewers may ignore page fragments. Page numbers are physical file pages, which can differ from printed labels.

TF-IDF provides a transparent baseline with no downloaded models or remote embedding calls. It is rebuilt per query, so this implementation favors a small local library over throughput. Arabic normalization helps lexical matching but does not translate questions or correct extraction order.

## Data flow and privacy

PDF bytes, extracted chunks and question history remain in SQLite unless the user explicitly selects generation. Only selected passages and the current question are sent to the model provider. Upload SHA-256 hashes prevent duplicate files. Parameterized SQL is used throughout. Browser output is constructed with textContent rather than interpreting document text as HTML.

The localhost binding, allowed-host list and cross-origin checks reduce accidental browser access. They are not authentication. Local processes can access the API. PDF parsing is not sandboxed. Public deployment requires authentication, authorization, resource-isolated ingestion, request limits, encryption and a privacy review.

## Failure behavior

Unreadable, encrypted or textless PDFs are rejected. Empty pages in otherwise usable documents are reported. No lexical matches produces an explicit no-evidence response. Provider timeouts, malformed responses and invalid citation IDs fall back to local excerpts. Prompt instructions treat documents as untrusted, but do not guarantee resistance to prompt injection.

## Test boundaries

API tests exercise upload, duplicate detection, scoped search, deletion, invalid input, history, browser isolation and mocked generation. No production load testing, live model evaluation or independent security audit has been performed.

## Next milestones

1. Add curated question/source labels from permission-cleared documents and report recall@k and citation support.
2. Compare lexical, embedding and hybrid retrieval on that same held-out set.
3. Move ingestion to resource-limited workers and cache indexes with deletion invalidation.
4. Add account-level ownership checks before considering hosted deployment.
