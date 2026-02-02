### Bugs:
1. ✅ FIXED (commit 750c9be) - When I purge Completed when there's several completed, It does purge everything in database but only removes 1 from the UI, hit button again, and another goes away.  If I refresh page, they all disappear.
   - Fixed: Changed WebSocket event handling to process all events instead of just the latest

### UI:
1. ✅ FIXED (commit 750c9be) - The View Agent Graphs button needs to be a different color (green maybe)
   - Changed to emerald green
2. ✅ FIXED (commit 750c9be) - I do not like placement of Batch Tasks and View Agent Graphs buttons.
   - Moved to top header, aligned horizontally with Purge buttons
3. ✅ FIXED (commit 750c9be) - Can you make these bottons a bit smaller, colored and maybe try them at top, aligned horizontally with the Purge buttons
   - Reduced button size (h-8, text-xs), added visual separators