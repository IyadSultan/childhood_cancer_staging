
openai GPT 4.5 with Deep Research: Read the Toronto childhood cancer staging guidelines and extract an organized json file for all types of childhood cancer with staging criteria listed, starting by disease name, then list of criteria used for staging, then stages with full explanation that are easy for an LLM to understand.

claude 3.5 sonnet thinking (agent) read @toronoto_staging.json and understand it, then start making a pediatric cancer staging module that takes in a medical note similar to @example.txt and do the following:
1- Identify which tumor of the list categories in @toronoto_staging.json is applicable, also extract the "EMR stage" if mentioned in the note, otherwsie make it .Not provided'.    if more than one stage identified then provide them separated by coma.
2- Find which criteria is present in the note for that particular cancer.  Also read the definitions and make sure you produce a summary that has all the needed information.
3- Then produce toronto stage after reading the stages and call it calculated stage.  Also provide the explanation for this staging.  If information insufficient say : information not adequate.  
4- Then save in a csv using file name, EMR stage and calcuculated stage, and explanation for the calculated stage.

*  use crewai to build agents and @OpenAI gpt-4o-mini as a model.
* save results to a csv.
* use  @crewai to see how to build agents
*  I am using windows
* use UV package to install pacakges. I made an environment called venv for you already.