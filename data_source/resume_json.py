import json
from llama_index.core import Document

def documents():
    with open("data/manish_details.json") as f:
        data = json.load(f)

    documents = []

    summary_text = f"{data['identity']['name']} — {data['summary']}"
    documents.append(Document(
        text=summary_text,
        metadata={"section": "profile_summary",
        "type": "identity"}
    ))


    for job in data["work_experience"]:
        responsibilities = "\n".join(f"- {r}" for r in job["responsibilities"])
        text = f"""
    Role: {job['title']} at {job['company']} ({job['start_date']} to {job['end_date']})
    Domain: {job['domain']}
    Tech: {', '.join(job['tech_stack'])}
    Responsibilities:
    {responsibilities}
        """.strip()
        documents.append(Document(
            text=text,
            metadata={
                "section": "work_experience",
                "company": job["company"],
                "domain": job["domain"],
                "tech_stack": job["tech_stack"],  # use for metadata filtering
            }
        ))

    skills_text = "\n".join(
        f"{category}: {', '.join(items)}"
        for category, items in data["skills"].items()
    )
    documents.append(Document(
        text=f"Skills and technologies:\n{skills_text}",
        metadata={"section": "skills"}
    ))

    # 4. AI/ML section as one doc
    ai = data["ai_and_ml"]
    formal = "\n".join(
        f"- {e['title']} ({e['domain']}): {e['description']}"
        for e in ai["formal_experience"]
    )
    tools = ", ".join(t["name"] for t in ai["current_ai_tool_usage"]["tools"])
    learning = ", ".join(ai["current_learning"])
    documents.append(Document(
        text=f"""
    AI & ML background:
    Formal experience:
    {formal}
    Currently using: {tools}
    Currently learning: {learning}
    Career interest: {ai['career_interest']}
        """.strip(),
        metadata={"section": "ai_ml"}
    ))

    # 5. Each education entry with thesis/project detail
    for edu in data["education"]:
        extra = ""
        if "thesis" in edu:
            t = edu["thesis"]
            extra = f"\nThesis: {t['title']} — {t['description']} Stack: {', '.join(t['tech_stack'])}"
        elif "final_project" in edu:
            p = edu["final_project"]
            extra = f"\nFinal project: {p['title']} — {p['description']}"
        documents.append(Document(
            text=f"{edu['degree']}, {edu['institution']} ({edu['year']}){extra}",
            metadata={"section": "education", "degree": edu["degree"]}
        ))

    # 6. Notable achievements — each as its own doc for precision retrieval
    for achievement in data["notable_achievements"]:
        documents.append(Document(
            text=f"{achievement['area']}: {achievement['description']}",
            metadata={"section": "achievement", "area": achievement["area"]}
        ))

    # 7. FAQ pairs — keep Q+A together, never split them
    for faq in data["faq"]:
        documents.append(Document(
            text=f"Q: {faq['question']}\nA: {faq['answer']}",
            metadata={"section": "faq"}
        ))

    return documents
