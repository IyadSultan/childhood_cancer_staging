from flask import Flask, render_template, request, session, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, RadioField, TextAreaField, FileField, SubmitField
from wtforms.validators import DataRequired
from crewai import Agent, Crew, Task
from langchain.tools import BaseTool, tool
from pdfminer.high_level import extract_text
from docx import Document
from markdownify import markdownify
from xhtml2pdf import pisa
from tavily import TavilyClient
import markdown
import os
from dotenv import load_dotenv
from flask_session import Session
from typing import Dict

# Load environment variables
load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Define the form
class PolicyForm(FlaskForm):
    policy_name = StringField('Policy Name', validators=[DataRequired()])
    originating_body = StringField('Originating Body', validators=[DataRequired()])
    approving_body = StringField('Approving Body', validators=[DataRequired()])
    is_new_policy = RadioField('Policy Type', choices=[('new', 'New'), ('revision', 'revision')], default='new', validators=[DataRequired()])
    instructions = TextAreaField('Instructions and Standards', validators=[DataRequired()])
    old_policy_file = FileField('Upload Old Policy (PDF or Word)')
    submit = SubmitField('Submit')

@tool
def research_regulations(query: str) -> str:
    """Research relevant healthcare regulations with references."""
    tavily_client = TavilyClient(api_key=os.getenv('TAVILY_API_KEY'))
    
    print(f"Searching Tavily for: {query}")
    
    # Perform Tavily search
    search_result = tavily_client.search(
        query=query,
        search_depth="advanced",
        include_domains=["who.int", "cdc.gov", "nih.gov", "jointcommission.org", "cms.gov"],
        include_answer=True,
        max_results=5
    )
    
    # Format the results with citations
    references = []
    content = f"Research findings for: {query}\n\n"
    
    if "answer" in search_result and search_result["answer"]:
        content += f"Summary: {search_result['answer']}\n\n"
    
    content += "References:\n"
    
    for i, result in enumerate(search_result.get("results", []), 1):
        title = result.get("title", "Untitled")
        url = result.get("url", "No URL")
        content += f"{i}. {title} - {url}\n"
        references.append({"title": title, "url": url})
    
    print(f"Found {len(references)} references from Tavily")
    
    return content

class ResearchAgent:
    def __init__(self):
        self.agent = Agent(
            role='Senior Research Analyst',
            goal='Conduct comprehensive research on healthcare regulations with references',
            backstory=(
                'Expert in healthcare policy research with a decade of experience '
                'analyzing regulatory frameworks and compliance requirements'
            ),
            tools=[research_regulations],
            verbose=True
        )

    def run_task(self, task):
        crew = Crew(agents=[self.agent], tasks=[task], verbose=True)
        result = crew.kickoff()
        return result.raw if hasattr(result, 'raw') else str(result)

    def research_policy_topic(self, policy_title: str, context: Dict = None) -> str:
        task = Task(
            description=f"""Research regulations and best practices related to: {policy_title}

Consider the following context:
{context or {}}

Focus on:
1. Relevant regulations and guidelines
2. Industry best practices
3. Implementation considerations
4. Recent developments in this area""",
            expected_output="Comprehensive research findings including relevant regulations and guidelines",
            agent=self.agent
        )
        return self.run_task(task)

@app.route('/', methods=['GET', 'POST'])
def index():
    form = PolicyForm()
    step = request.form.get('step', '1')

    if request.method == 'POST':
        if step == '1' and form.validate_on_submit():
            # Step 1: Process initial form submission and optional old policy conversion
            old_policy_md = ''
            if form.old_policy_file.data:
                file = form.old_policy_file.data
                if file.filename.endswith('.pdf'):
                    text = extract_text(file.stream)
                    old_policy_md = markdownify(text)
                elif file.filename.endswith('.docx'):
                    doc = Document(file.stream)
                    text = '\n'.join([para.text for para in doc.paragraphs])
                    old_policy_md = markdownify(text)

            # Run research task using ResearchAgent
            research_agent = ResearchAgent()
            research_result = research_agent.research_policy_topic(
                policy_title=form.policy_name.data,
                context={
                    "originating_body": form.originating_body.data,
                    "approving_body": form.approving_body.data,
                    "policy_type": form.is_new_policy.data,
                    "instructions": form.instructions.data,
                    "old_policy": old_policy_md
                }
            )

            # Generate clarifying questions and a preliminary outline using a separate agent
            question_agent = Agent(
                role='Policy Clarification Expert',
                goal='Generate clarifying questions to gather additional input for drafting the final policy.',
                backstory='Expert in healthcare policy development and stakeholder engagement.',
                verbose=True
            )
            question_task = Task(
                description=f"""Based on the following research findings and policy context, generate a list of clarifying questions for the user to refine the final policy.
Policy Context:
- Policy Name: {form.policy_name.data}
- Originating Body: {form.originating_body.data}
- Approving Body: {form.approving_body.data}
- Policy Type: {form.is_new_policy.data}
- Instructions: {form.instructions.data}
- Old Policy (if any): {old_policy_md}

Research Findings:
{research_result}

Format the output with the following markers:
--- QUESTIONS ---
[List each question on a new line]
--- OUTLINE ---
[Provide a preliminary outline of the policy draft with section headers and bullet points]

Only include clarifying questions and a concise outline.""",
                expected_output="A list of clarifying questions and a preliminary outline, separated by markers.",
                agent=question_agent
            )
            crew_questions = Crew(agents=[question_agent], tasks=[question_task], verbose=True)
            question_output = crew_questions.kickoff().tasks_output[-1].raw

            # Split the output into questions and outline
            parts = question_output.split('--- QUESTIONS ---')
            questions_section = parts[1] if len(parts) > 1 else ""
            parts2 = questions_section.split('--- OUTLINE ---')
            questions_text = parts2[0].strip()
            outline_text = parts2[1].strip() if len(parts2) > 1 else ""

            questions_list = [q.strip() for q in questions_text.split('\n') if q.strip()]

            # Save research, outline, questions, and form data in session
            session['research'] = research_result
            session['outline'] = outline_text
            session['questions'] = questions_list
            session['form_data'] = {
                'policy_name': form.policy_name.data,
                'originating_body': form.originating_body.data,
                'approving_body': form.approving_body.data,
                'instructions': form.instructions.data,
                'old_policy': old_policy_md,
                'policy_type': form.is_new_policy.data
            }

            # Create a preview combining research summary and outline for the user
            preview_content = f"### Research Summary\n\n{research_result}\n\n### Preliminary Outline\n\n{outline_text}"
            preview_html = markdown.markdown(preview_content)

            # Render Step 2: Display clarifying questions with preview
            return render_template('index.html', step='2', preview_html=preview_html, questions=questions_list)

        elif step == '2':
            # Step 2: Process the user’s answers and draft the final policy
            form_data = session.get('form_data', {})
            research_result = session.get('research', '')
            outline_text = session.get('outline', '')
            questions = session.get('questions', [])
            answers = [request.form.get(f'answer_{i+1}', '') for i in range(len(questions))]
            qa_pairs = "\n".join([f"Q: {q}\nA: {a}" for q, a in zip(questions, answers)])

            final_agent = Agent(
                role='Policy Writer',
                goal='Draft the final healthcare policy based on research, user input, and policy context.',
                backstory='Specialist in creating compliant healthcare policies with attention to detail and regulatory requirements.',
                verbose=True
            )
            final_task = Task(
                description=f"""Using the following information, draft the final policy in the KHCC format.

Policy Context:
- Policy Name: {form_data.get('policy_name')}
- Originating Body: {form_data.get('originating_body')}
- Approving Body: {form_data.get('approving_body')}
- Policy Type: {form_data.get('policy_type')}
- Instructions: {form_data.get('instructions')}
- Old Policy (if any): {form_data.get('old_policy')}

Research Findings:
{research_result}

Preliminary Outline:
{outline_text}

User Answers:
{qa_pairs}

The final policy should include these sections:
- Title
- Purpose
- Policy Statement
- Scope
- Responsibilities
- Definitions
- Procedures
- Documentation Requirements
- References (include inline citations with hyperlinks to the sources from the research findings)
- Document Historic Track
- Approval and Implementation

Ensure the content follows KHCC standards and includes clear references.""",
                expected_output="A complete final policy draft in markdown format following the KHCC structure, including a References section with hyperlinks.",
                agent=final_agent
            )
            crew_final = Crew(agents=[final_agent], tasks=[final_task], verbose=True)
            final_policy_md = crew_final.kickoff().tasks_output[-1].raw

            # Store the final policy markdown in session and render the editable HTML preview (Step 3)
            session['final_policy_md'] = final_policy_md
            preview_html = markdown.markdown(final_policy_md)
            return render_template('index.html', step='3', final_policy_md=final_policy_md, preview_html=preview_html)

        elif step == '3':
            # Step 3: User edits the final policy HTML version; on submission, generate PDF.
            edited_policy_md = request.form.get('edited_policy_md', '')
            if not edited_policy_md:
                edited_policy_md = session.get('final_policy_md', '')
            # Generate HTML content from the (possibly) edited markdown
            html_content = f"<html><body>{markdown.markdown(edited_policy_md)}</body></html>"
            pdf_path = os.path.join('static', 'policy.pdf')
            with open(pdf_path, "wb") as pdf_file:
                pisa_status = pisa.CreatePDF(html_content, dest=pdf_file)
                if pisa_status.err:
                    return "Error generating PDF", 500
            return render_template('index.html', step='4', download_link=url_for('static', filename='policy.pdf'), final_policy_html=markdown.markdown(edited_policy_md))

        elif step == '4':
            # Optional: Directly display PDF download step if needed.
            download_link = request.args.get('download_link', url_for('static', filename='policy.pdf'))
            return render_template('index.html', step='4', download_link=download_link)

    # Default: Render Step 1 form
    return render_template('index.html', step='1', form=form)

if __name__ == '__main__':
    if not os.path.exists('static'):
        os.makedirs('static')
    app.run(debug=True)