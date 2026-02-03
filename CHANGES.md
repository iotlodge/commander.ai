### Changes Needed:
1. Drop "Tool Call" column or Rename to "Feedback Requested."
   2. Objective: When an Agent/Task needs User input, the card should appear in "Feedback Requested" with request from graph and input (within card) to be sent back to active task running in background flow.
2. Track Tool Calls for each Task. As a (ToDo): add tracking of Tool Calls, Agent Calls, Total Tokens on each Task Card along with % of progress.
3. To left of Command input field, add 2 Buttons:
   4. "Batch Tasks" - This will be used to Batch requests, later when we have detailed LLM Flows.
   5. "View Agent Graphs" - This I want now and here's how I believe it can be done (unless you have better way)
      6. Each compiled graph (every agent always has one) can generate (plot/print mermaid) into a Database table (e.g. 'active_graphs'), by agent "nickname"
         7. It is Good if it is upserted each time the graph is compiled.
      7. When Button in front end is pressed:
         8. Open a frameless window (if possible) and show a (same CSS) nice Panel or something for Each Agent and render the Graph image (mermaid or something)

New as of 02-02-2026:
1. 


### Feedback on UI:
1. read PROJECT_OBJECTIVE.md
2. Use your UI Design experience to continuously improve the usability of the UI
   3. Optimize placement and size of cards, columns, text input fields and text areas, as we adjust design

