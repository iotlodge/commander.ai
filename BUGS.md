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
4. ✅ FIXED - The Board's minimum width is still just a bit too wide (scrollbar appears [needs to be about 5-10% less overall]).  Try making each of the columns width (cards if necessary) smaller or adjust so columns resize without a board scrollbar
   - Reduced column width from 320px to 315px
5. Reference BUG_image:
   6. ✅ FIXED (commits d3dbff1) - Bug A: when the agent is highlighted, the font should be more readable (almost disappears)
      - Used Tailwind group modifier: group-data-[selected=true]:text-gray-900
      - @agent text now dark gray (gray-900) on white background when selected
      - All text elements properly styled with dark colors when highlighted
   7. ✅ FIXED (commits a7c33ce, aff7bea) - Bug B: when I click inside command window, the popup comes up (good), BUT when I select the agent to talk to it does not enter @name in the command window. It should enter the agent's name so I can then enter the command
      - Added 10ms delay before closing autocomplete to ensure text insertion
      - Supports two use cases:
        * Type '@b' then select → replaces '@b' with '@bob '
        * Click in empty field then select → inserts '@bob ' at cursor
      - No need to type @ manually since autocomplete appears automatically

