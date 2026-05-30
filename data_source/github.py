import requests
import base64
import os
from llama_index.core import Document

GITHUB_USER = "maniz-stha"
HEADERS = {"Authorization": os.getenv("GITHUB_ACCESS_TOKEN")}

TIMEOUT = 15  # seconds per request

def fetch_profile():
    r = requests.get(f"https://api.github.com/users/{GITHUB_USER}", headers=HEADERS, timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()

def fetch_repos():
    repos = []
    page = 1
    while True:
        r = requests.get(
            f"https://api.github.com/users/{GITHUB_USER}/repos",
            params={"sort": "updated", "per_page": 100, "page": page},
            headers=HEADERS,
            timeout=TIMEOUT
        )
        r.raise_for_status()
        batch = r.json()
        if not isinstance(batch, list) or not batch:
            break
        repos.extend(batch)
        page += 1
    return repos

def fetch_languages(repo_full_name):
    r = requests.get(f"https://api.github.com/repos/{repo_full_name}/languages", headers=HEADERS, timeout=TIMEOUT)
    return r.json() if r.status_code == 200 else {}

def fetch_readme(repo_full_name):
    r = requests.get(f"https://api.github.com/repos/{repo_full_name}/readme", headers=HEADERS, timeout=TIMEOUT)
    if r.status_code == 200:
        content = r.json().get("content", "")
        return base64.b64decode(content).decode("utf-8", errors="ignore")
    return None

def build_data():
    profile = fetch_profile()
    repos = fetch_repos()

    data = {
        "github_profile": {
            "username": profile.get("login"),
            "bio": profile.get("bio"),
            "public_repos": profile.get("public_repos"),
            "followers": profile.get("followers"),
            "url": profile.get("html_url")
        },
        "repositories": []
    }

    for repo in repos:
        if repo["fork"]:  # skip forks, they're not your work
            continue

        languages = fetch_languages(repo["full_name"])
        readme = fetch_readme(repo["full_name"])

        data["repositories"].append({
            "name": repo["name"],
            "description": repo.get("description"),
            "url": repo["html_url"],
            "topics": repo.get("topics", []),
            "languages": languages,
            "primary_language": repo.get("language"),
            "stars": repo.get("stargazers_count"),
            "updated_at": repo.get("updated_at"),
            "readme_snippet": readme[:500] if readme else None  # first 500 chars
        })
    return data

def documents():
    github = build_data()
    documents = []

    profile_text = "\n".join(f"- {r}: {github['github_profile'][r]}" for r in github['github_profile'])
    documents.append(Document(
        text=profile_text,
        metadata={
            "section": "github_profile"
        }
    ))
    for repo in github["repositories"]:
        # if not repo.get("description") and not repo.get("readme_snippet"):
        #     continue  # skip empty repos, they add noise

        langs = ", ".join(repo.get("languages", {}).keys())
        topics = ", ".join(repo.get("topics", []))
        readme = repo.get("readme_snippet", "") or ""

        text = f"""
    GitHub Repository: {repo['name']}
    Description: {repo.get('description', 'N/A')}
    Languages: {langs}
    Topics: {topics}
    {('README: ' + readme[:400]) if readme else ''}
        """.strip()

        documents.append(Document(
            text=text,
            metadata={
                "section": "github_repo",
                "repo": repo["name"],
                "primary_language": repo.get("primary_language"),
                "topics": repo.get("topics", []),
            }
        ))
    return documents
