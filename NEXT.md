# Next Steps - Commander.ai

## Priority: Mature DocumentManager Agent (Alice) 🎯

**Goal**: Make Alice world-class for document operations - she should handle ANYTHING related to documents, files, and collections.

**Current Capabilities**:
- ✅ Load documents into collections (PDF, DOCX, TXT, MD)
- ✅ Semantic search across collections (Qdrant)
- ✅ Web search (Tavily API)
- ✅ Collection management (create, delete, list)
- ✅ LLM reasoning for flexible task handling
- ✅ Website crawling and content extraction

**Missing Capabilities** (Required for world-class status):
- ❌ File system operations (find, archive, delete files by age/pattern)
- ❌ File metadata queries (modification dates, sizes, types)
- ❌ Batch operations (archive all files older than X months)
- ❌ Database queries (check for deprecated models in approved_models_provider)
- ❌ Performance stats aggregation (run backend jobs)
- ❌ Cross-store operations (database + Qdrant + file system)

**Implementation Plan**:

### Phase 1: Expand Alice's Toolkit
1. **File System Tool** - Add tool for:
   - List files by pattern/age/size
   - Move/copy/archive files
   - Check file metadata (mtime, size, type)
   - Batch operations

2. **Database Query Tool** - Add direct database access:
   - Query approved_models_provider for deprecation checks
   - Access performance_scores for aggregation
   - Read agent_model_configs for current status

3. **Backend Job Tool** - Add capability to trigger:
   - Performance stats aggregation job
   - Model deprecation checks
   - Collection cleanup/optimization

### Phase 2: Update LLM Reasoning
- Add new action types to llm_reasoning_node:
  - "file_system_operation"
  - "database_query"
  - "backend_job"
- Update prompt with examples for these actions

### Phase 3: Update Quick Actions
- Remove invalid actions ("Archive old files" until capabilities added)
- Add actions Alice can actually do:
  - "Search for files by pattern"
  - "List recent documents"
  - "Check collection sizes"
  - "Search web and summarize"

### Phase 4: Testing
- Test all Quick Actions end-to-end
- Verify file system operations are safe (no destructive actions without confirmation)
- Ensure database queries are read-only (unless explicitly authorized)

**Success Criteria**:
- ✅ Alice can find and archive files by age/pattern
- ✅ Alice can check for deprecated models directly (database + web)
- ✅ Alice can aggregate performance stats
- ✅ All Quick Actions work as advertised
- ✅ Alice handles ANY document-related task intelligently

---

## Completed Today (February 6, 2026) 🎉

### Three Major Releases:
1. **v0.3.0** - Live Prompt Engineering
2. **v0.4.0** - Multi-Provider LLM Switching
3. **v0.5.0** - Complete Performance & Intelligence System

### Additional Achievements:
- Fixed all "parent" vs "agent_parent" ID inconsistencies
- Added LLM reasoning to Alice for flexible task handling
- Fixed feedback widget UX (one-click star rating)
- Fixed web search storage logic (skip when no collection specified)
- 100% test pass rate (36/36 tests)
- All features merged to main and deployed

**Total Impact**: Three production-ready major features in one day! 🚀

---

## Future Enhancements (Lower Priority)

- Debug peer evaluation JSON parsing (Kai/Maya prompts)
- Category-specific performance rankings
- Trend alerts for agent degradation
- Prompt marketplace (share optimized prompts)
- Multi-agent collaboration workflows
