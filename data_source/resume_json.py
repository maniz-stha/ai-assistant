import json
from llama_index.core import Document

def documents():
    with open("data/manish_details.json") as f:
        data = json.load(f)

    documents = []

    # 1. Identity & Contact Info
    identity = data["identity"]
    contact = identity["contact"]
    identity_text = f"""
    Name: {identity['name']}
    Title: {identity['title']}
    Tagline: {identity['tagline']}
    Location: {identity['location']} ({identity['timezone']})
    Contact Information:
    - Email: {contact['email']}
    - LinkedIn: {contact['linkedin']}
    - Portfolio: {contact['portfolio']}
    - GitHub: {contact['github']}
    """.strip()
    documents.append(Document(
        text=identity_text,
        metadata={"section": "identity", "type": "contact_info"}
    ))

    # 2. Summary & Overview
    summary_text = f"Professional Summary:\n{data['summary']}\nTotal Years of Experience: {data['years_of_experience']}"
    documents.append(Document(
        text=summary_text,
        metadata={"section": "summary"}
    ))

    # 3. Core Competencies
    competencies_text = "Core Competencies and Key Strengths:\n" + "\n".join(f"- {c}" for c in data["core_competencies"])
    documents.append(Document(
        text=competencies_text,
        metadata={"section": "core_competencies"}
    ))

    # 4. Detailed Skills
    for category, items in data["skills"].items():
        text = f"Skills - {category.replace('_', ' ').title()}:\n" + ", ".join(items)
        documents.append(Document(
            text=text,
            metadata={"section": "skills", "category": category}
        ))

    # 5. Work Experience
    for job in data["work_experience"]:
        responsibilities = "\n".join(f"- {r}" for r in job["responsibilities"])
        text = f"""
    Job Title: {job['title']}
    Company: {job['company']}
    Location: {job['location']} ({job['work_type']})
    Duration: {job['start_date']} to {job['end_date']} ({job['duration_years']} years)
    Domain: {job['domain']}
    Tech Stack: {', '.join(job['tech_stack'])}
    Responsibilities:
    {responsibilities}
        """.strip()
        documents.append(Document(
            text=text,
            metadata={
                "section": "work_experience",
                "company": job["company"],
                "domain": job["domain"],
                "tech_stack": job["tech_stack"],
            }
        ))

    # 6. Freelance Projects
    for project in data["freelance_projects"]:
        text = f"""
    Freelance Project for {project['client']}
    Description: {project['description']}
    Tech Stack: {', '.join(project['tech_stack'])}
        """.strip()
        documents.append(Document(
            text=text,
            metadata={"section": "freelance", "client": project["client"]}
        ))

    # 7. Domain Experience
    for domain in data["domain_experience"]:
        highlights = "\n".join(f"- {h}" for h in domain["highlights"])
        text = f"""
    Domain Expertise: {domain['domain']}
    Companies: {', '.join(domain['companies'])}
    Highlights:
    {highlights}
        """.strip()
        documents.append(Document(
            text=text,
            metadata={"section": "domain_experience", "domain": domain["domain"]}
        ))

    # 8. AI/ML Deep Dive
    ai = data["ai_and_ml"]
    formal = "\n".join(
        f"- {e['title']} ({e['domain']}): {e['description']} [Tech: {', '.join(e.get('tech_stack', []))}]"
        for e in ai["formal_experience"]
    )
    tools = "\n".join(
        f"- {t['name']} ({t['provider']}): {', '.join(t['use_cases'])}" 
        for t in ai["current_ai_tool_usage"]["tools"]
    )
    learning = ", ".join(ai["current_learning"])
    ai_text = f"""
    AI & ML Background and Career Interest:
    Summary: {ai['summary']}
    
    Formal Academic Experience:
    {formal}
    
    Current AI Tooling Usage:
    {tools}
    
    Active Learning: {learning}
    Career Goal: {ai['career_interest']}
    """.strip()
    documents.append(Document(
        text=ai_text,
        metadata={"section": "ai_ml_detailed"}
    ))

    # 9. Career Goals & Transition
    goals = data["career_goals"]
    strengths = "\n".join(f"- {s}" for s in goals["strengths_for_ai_roles"])
    goals_text = f"""
    Career Goals:
    Current Focus: {goals['current_focus']}
    Target Roles: {', '.join(goals['target_roles'])}
    Transition Strategy: {goals['transition_direction']}
    Strengths for AI Roles:
    {strengths}
    """.strip()
    documents.append(Document(
        text=goals_text,
        metadata={"section": "career_goals"}
    ))

    # 10. Education
    for edu in data["education"]:
        extra = ""
        if "thesis" in edu:
            t = edu["thesis"]
            extra = f"\n{t['type']}: {t['title']}\nDomain: {t['domain']}\nDescription: {t['description']}\nStack: {', '.join(t['tech_stack'])}"
        elif "final_project" in edu:
            p = edu["final_project"]
            extra = f"\n{p['type']}: {p['title']}\nDomain: {p['domain']}\nDescription: {p['description']}\nStack: {', '.join(p['tech_stack'])}"
        
        text = f"{edu['degree']} from {edu['institution']}, {edu['location']} ({edu['year']}){extra}"
        documents.append(Document(
            text=text,
            metadata={"section": "education", "degree": edu["degree"]}
        ))

    # 11. Notable Achievements
    for achievement in data["notable_achievements"]:
        documents.append(Document(
            text=f"Notable Achievement in {achievement['area']}: {achievement['description']}",
            metadata={"section": "achievement", "area": achievement["area"]}
        ))

    # 12. Work Style & Preferences
    style_text = "Work Style and Professional Preferences:\n" + "\n".join(f"- {s}" for s in data["work_style"])
    documents.append(Document(
        text=style_text,
        metadata={"section": "work_style"}
    ))

    # 13. FAQ Pairs
    for faq in data["faq"]:
        documents.append(Document(
            text=f"Question: {faq['question']}\nAnswer: {faq['answer']}",
            metadata={"section": "faq"}
        ))

    return documents
