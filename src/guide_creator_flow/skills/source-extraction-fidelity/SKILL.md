---
name: source-extraction-fidelity
description: Fidelity rules for extracting content from source material — quote code exactly, preserve verbatim benchmark figures, and flag unreadable sources rather than guessing. Use when scraping web pages, reading local documents, or analysing research papers for the research report.
---

Apply these rules when extracting content from any source (web page, local document, or research paper):

- **Quote code exactly — never paraphrase.** When a source contains a code snippet, command, or configuration block, reproduce it verbatim. Do not rewrite, summarize, or "clean up" code from a source.
- **Preserve verbatim benchmark figures.** Numeric results, benchmark tables, and performance figures must be extracted exactly as written in the source. Never round, estimate, or summarize away the numbers — exact figures matter.
- **Flag unreadable sources.** If a page cannot be scraped, a file cannot be read, or content is paywalled, bot-blocked, truncated, or otherwise inaccessible, state this explicitly rather than guessing at what it might contain.
