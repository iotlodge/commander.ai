CORE OBJECTIVE:
Ability to edit the underline LLM + Provider (OpenAI, Anthorpic, HuggingFace).

At a high level were tweaking the UI, maybe adding an edit modal for agents and their active models, some might have MORE in their graph.  A new database table and a way to recycle backend elements clean.


Database:
create a table to contain approved_models_provider, seed this with a script and include well know 
[logic, reasoning, routing, planning, etc.] etc. = I want you to recommend great models for the purpose of project

The table should have several fields, outside of obvious ('version':str, 'model_name':str, 'approved':bool, 'mode':str, 'date':datetime), consider lifecycle management or maybe a rollback button. Feel free to impress me here.

Here's How I want the Experience to work:
From the setting icon, on each agent tab, we need a place to Edit LLM and Provider [later in file]

Image Sources:
https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/openai-light.svg
https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/openai.svg
https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/svg/hugging-face.svg
![Anthropic_Logo_dark.svg](images/Anthropic_Logo_dark.svg)
![Anthropic_Logo_light.svg](images/Anthropic_Logo_light.svg)

Location: Main UI
On the Agent Tile (left side)
@name ('model_name') 'small_provider_icon' 
agent_role 

('gpt-4') as example for model name.. the text you would put into model='foo':
INSTALLED: I did run 'uv add langchain-anthropic' and validated the following in a test.
llm = ChatAnthropic(
    model="claude-3-haiku-20240307",
    temperature=0
)
icon of provider correct for theme, and if possible not big.  @name and agent_role, are in place.  If you run into problems making it look good, we can use nice text as a fallback, but it is one or the other.

Behavior:
When underline model or LLM are changed, the Graph will need to reload smoothly; it is best to only reload the impacted agent, if it's possible to test before activating somehow(super), if possible. Regardless, the agent being changed should have no active jobs before it is reloaded.

Edit of LLM and/or Provider.
YOU OWN THIS SPACE because you ROCK at UIs.
My Thoughts: Putting it inside the settings modal, where we edit prompts, could get confusing.  My thought is to create a "Agent Models"

If the UI gives you issues, focus on activation from settings icon and maybe a NICE hover to show active LLMs and Providers (I THINK I like this better but you chose), and a GREAT Modal to edit.  Might be less complex also..