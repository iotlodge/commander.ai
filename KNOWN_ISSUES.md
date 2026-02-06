# Known Issues

## Prompt Management UI

### @leo Modal Width Issue (Low Priority - Cosmetic)

**Status**: Open
**Severity**: Low (UX polish)
**Added**: February 6, 2026

**Description**:
The Prompt Management modal for @leo (Orchestrator) shows content clipping on the right side. Text like "Showing 1 of 1 prompts" appears as "Showing 1 of 1 promp" with the "ts" cut off.

**Impact**:
- Functionality: ✅ Fully working
- UX: Minor annoyance - text truncation on right edge
- Other agents (@bob, @sue, @rex, @alice, @maya, @kai, @chat): ✅ Display correctly

**Reproduction**:
1. Open Mission Control
2. Hover over @leo agent card
3. Click ⚙️ Settings icon
4. Observe right-side text clipping in modal

**What We've Tried**:
- Increased modal width: `max-w-4xl` → `max-w-5xl` → `max-w-6xl`
- Added `overflow-x-hidden` to prevent scrollbars
- Added `w-full` constraints to all child elements
- Reduced padding: `p-6` → `p-4`
- Added `truncate` to long titles
- Moved "Showing X of Y prompts" to separate row
- Multiple dev server restarts with cache clearing

**Hypothesis**:
Likely a CSS specificity issue or shadcn/ui Dialog component internal styling that's only triggered by @leo's specific content/title length. Other agents don't exhibit this behavior.

**Next Steps** (when revisiting):
1. Inspect computed styles in browser DevTools on @leo modal
2. Compare DOM structure between @leo and @bob modals
3. Check if DialogContent has internal max-width overrides
4. Consider custom Dialog wrapper without shadcn constraints
5. Possible nuclear option: Use raw Radix UI Dialog without shadcn wrapper

**Workaround**:
None needed - functionality is perfect, just slight visual imperfection on one agent's modal.

---

**Note**: This is a v0.3.0 polish item. Core Prompt Engineering functionality is production-ready and working excellently across all agents.
