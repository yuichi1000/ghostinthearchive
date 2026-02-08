# Agent Catalog

All ADK agents in the project with their properties and expected eval scenarios.

## Archive Pipeline (`archive_agents/`)

Pipeline order: Librarian → Scholar → Storyteller → Illustrator → Publisher

Curator is a standalone agent (not in the sequential pipeline).

### Librarian

| Property | Value |
|----------|-------|
| Module | `archive_agents/agents/librarian.py` |
| Variable | `librarian_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `collected_documents` |
| Tools | `search_newspapers`, `search_archives`, `get_available_keywords` |
| Predecessor | (none — first agent) |
| Checks Marker | (none) |
| Emits Marker | `NO_DOCUMENTS_FOUND` |
| Placeholders | (none) |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `librarian_basic_search` | Basic historical document search | `search_newspapers`, `search_archives` | `collected_documents total_found` |
| `librarian_folklore_search` | Folklore/legend search with keyword discovery | `get_available_keywords`, `search_newspapers` | `ghost legend folklore` |
| `librarian_no_results` | No documents found (impossible query) | `search_newspapers` | `NO_DOCUMENTS_FOUND` |
| `librarian_bilingual_expansion` | Bilingual (English + Spanish) search | `search_newspapers`, `search_archives` | `sources_searched` |

---

### Scholar

| Property | Value |
|----------|-------|
| Module | `archive_agents/agents/scholar.py` |
| Variable | `scholar_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `mystery_report` |
| Tools | (none) |
| Predecessor | Librarian (`collected_documents`) |
| Checks Marker | `NO_DOCUMENTS_FOUND` |
| Emits Marker | `INSUFFICIENT_DATA` |
| Placeholders | `{collected_documents}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `scholar_fact_based_analysis` | Historical fact analysis with date/event discrepancies | `[]` | `mystery_report DATE_MISMATCH` |
| `scholar_folklore_analysis` | Folklore anomaly analysis (recurring patterns, taboos) | `[]` | `Folkloric Context RECURRING_PATTERN` |
| `scholar_anthropological_analysis` | Cultural anthropology analysis (power structures, rituals) | `[]` | `Anthropological Context POWER_ERASURE` |
| `scholar_insufficient_data` | Insufficient data handling | `[]` | `INSUFFICIENT_DATA NO_DOCUMENTS_FOUND` |
| `scholar_cross_reference_analysis` | Cross-reference of fact, folklore, and anthropology | `[]` | `Folkloric Context Anthropological Context` |

---

### Storyteller

| Property | Value |
|----------|-------|
| Module | `archive_agents/agents/storyteller.py` |
| Variable | `storyteller_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `creative_content` |
| Tools | (none) |
| Predecessor | Scholar (`mystery_report`) |
| Checks Marker | `INSUFFICIENT_DATA` |
| Emits Marker | `NO_CONTENT` |
| Placeholders | `{mystery_report}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `storyteller_complete_narrative` | Full blog article generation | `[]` | `creative_content Sources Firestore` |
| `storyteller_fact_folklore_balance` | Balance of historical fact and folklore elements | `[]` | `伝説 記録 Firestore` |
| `storyteller_four_part_structure` | Four-part narrative structure (discovery, evidence, context, mystery) | `[]` | `アーカイブ Sources Firestore` |
| `storyteller_insufficient_data` | NO_CONTENT emission on insufficient input | `[]` | `NO_CONTENT INSUFFICIENT_DATA` |

---

### Illustrator

| Property | Value |
|----------|-------|
| Module | `archive_agents/agents/illustrator.py` |
| Variable | `illustrator_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `visual_assets` |
| Tools | `generate_image` |
| Predecessor | Storyteller (`creative_content`) |
| Checks Marker | `NO_CONTENT` |
| Emits Marker | (none) |
| Placeholders | `{creative_content}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `illustrator_fact_style` | Fact-based image (white/black photo style) | `generate_image` | `visual_assets Fact` |
| `illustrator_folklore_style` | Folklore-based image (19th-century engraving style) | `generate_image` | `visual_assets Folklore` |
| `illustrator_no_content_skip` | Skip generation when NO_CONTENT | `[]` | `NO_CONTENT` |

---

### Publisher

| Property | Value |
|----------|-------|
| Module | `archive_agents/agents/publisher.py` |
| Variable | `publisher_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `published_episode` |
| Tools | `upload_images`, `publish_mystery` |
| Predecessor | Illustrator (`visual_assets`) + all upstream keys |
| Checks Marker | All upstream markers (`NO_DOCUMENTS_FOUND`, `INSUFFICIENT_DATA`, `NO_CONTENT`) |
| Emits Marker | (none) |
| Placeholders | `{collected_documents}`, `{mystery_report}`, `{creative_content}`, `{visual_assets}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `publisher_full_workflow` | Full publish workflow with image upload | `upload_images`, `publish_mystery` | `published_episode Firestore mystery_id` |
| `publisher_document_structure` | Verify required Firestore fields | `publish_mystery` | `mystery_id status Firestore` |
| `publisher_failure_handling` | Skip publish when upstream failures detected | `[]` | `INSUFFICIENT_DATA NO_CONTENT` |

---

### Curator

| Property | Value |
|----------|-------|
| Module | `archive_agents/agents/curator.py` |
| Variable | `curator_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `suggested_themes` |
| Tools | (none) |
| Predecessor | (standalone — not in sequential pipeline) |
| Checks Marker | (none) |
| Emits Marker | (none) |
| Placeholders | `{existing_titles}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `curator_theme_suggestion` | Generate investigation themes | `[]` | `suggested_themes Fact Folklore` |
| `curator_duplicate_avoidance` | Avoid suggesting existing titles | `[]` | `suggested_themes 重複なし` |

---

## Podcast Pipeline (`podcast_agents/`)

Pipeline order: Scriptwriter → Producer

### Scriptwriter

| Property | Value |
|----------|-------|
| Module | `podcast_agents/agents/scriptwriter.py` |
| Variable | `scriptwriter_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `podcast_script` |
| Tools | (none) |
| Predecessor | (reads `creative_content` from Firestore pre-set) |
| Checks Marker | `NO_CONTENT` |
| Emits Marker | `NO_SCRIPT` |
| Placeholders | `{creative_content}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `scriptwriter_complete_script` | Full podcast script generation | `[]` | `podcast_script INTRO OUTRO` |
| `scriptwriter_segment_structure` | Verify INTRO/SEGMENTS/OUTRO structure | `[]` | `INTRO SEGMENTS OUTRO` |
| `scriptwriter_no_content_failure` | NO_SCRIPT emission on NO_CONTENT input | `[]` | `NO_SCRIPT NO_CONTENT` |

---

### Producer

| Property | Value |
|----------|-------|
| Module | `podcast_agents/agents/producer.py` |
| Variable | `producer_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `audio_assets` |
| Tools | (none) |
| Predecessor | Scriptwriter (`podcast_script`) |
| Checks Marker | (none) |
| Emits Marker | (none) |
| Placeholders | `{podcast_script}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `producer_audio_plan` | Audio production plan generation | `[]` | `audio_assets voice SFX` |
| `producer_bilingual_text` | Bilingual (Japanese/English) text segments | `[]` | `bilingual 日本語 English` |
| `producer_voice_sfx_settings` | Voice and SFX configuration | `[]` | `voice SFX BGM` |

---

## Translator Pipeline (`translator_agents/`)

### Translator

| Property | Value |
|----------|-------|
| Module | `translator_agents/agents/translator.py` |
| Variable | `translator_agent` |
| Model | `gemini-3-pro-preview` |
| Output Key | `translation_result` |
| Tools | (none) |
| Predecessor | (reads from Firestore pre-set fields) |
| Checks Marker | `NO_CONTENT` |
| Emits Marker | `NO_TRANSLATION` |
| Placeholders | `{title}`, `{summary}`, `{narrative_content}`, `{discrepancy_detected}`, `{hypothesis}`, `{alternative_hypotheses}`, `{political_climate}`, `{story_hooks}` |

**Eval Scenarios:**

| eval_id | Description | tool_uses | final_response keywords |
|---------|-------------|-----------|------------------------|
| `translator_complete_translation` | Full Japanese-to-English translation | `[]` | `translation_result title_en summary_en narrative_content_en` |
| `translator_no_content_skip` | NO_TRANSLATION emission on NO_CONTENT input | `[]` | `NO_TRANSLATION NO_CONTENT` |
| `translator_json_output_format` | Verify JSON output structure with _en fields | `[]` | `translation_result JSON title_en` |

---

## Maintenance

When adding a new agent to any pipeline:

1. Add the agent definition to this catalog following the same table format
2. Run `/gen-eval` for the new agent to generate eval tests
3. Verify all tests pass with `pytest tests/eval/ tests/integration/ -v`
