#!/usr/bin/env python3
"""
GitHub Scout — scans GitHub for best repos, finds trends, catalogs discoveries.

Used by the 'scout' cron job profile. Outputs JSON for the LLM to analyze.
Supports multiple modes:
  --starred       Check user's starred repos for new ones
  --trending      Get today's trending repos (by language/category)
  --search TERM   Search GitHub for repos matching a query
  --builders      Scan for best builder/AI-agent/automation repos
  --categories    Scan across all our tracked categories
  --repo URL      Deep-scan a specific repo
"""

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

# === CONFIG ===
TRACKED_CATEGORIES = {
    "ai-agents": [
        "ai agent framework", "autonomous agent", "multi-agent system",
        "agent orchestration", "llm agent", "coding agent"
    ],
    "dev-tools": [
        "developer tool", "cli framework", "terminal tool",
        "build tool", "devops automation"
    ],
    "ml-infra": [
        "llm inference", "model serving", "fine-tuning framework",
        "mlops platform", "vector database"
    ],
    "research": [
        "research tool", "paper implementation", "benchmark framework",
        "evaluation harness", "scientific computing"
    ],
    "data-eng": [
        "data pipeline", "etl framework", "data processing",
        "real-time analytics", "stream processing"
    ],
}

OUTPUT_DIR = Path.home() / ".hermes" / "scout_data"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def gh_search(query: str, limit: int = 10, sort: str = "stars") -> list[dict]:
    """Search GitHub repos using gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "search", "repos", query,
             "--sort", sort,
             "--limit", str(limit),
             "--json", "name,owner,url,stargazersCount,language,description,updatedAt,topics,fork"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return [{"error": result.stderr.strip(), "query": query}]
        repos = json.loads(result.stdout)
        for r in repos:
            r["_scanned_at"] = datetime.now(timezone.utc).isoformat()
        return repos
    except Exception as e:
        return [{"error": str(e), "query": query}]


def gh_starred(limit: int = 50) -> list[dict]:
    """Get user's starred repos via gh CLI."""
    try:
        result = subprocess.run(
            ["gh", "api", f"/user/starred?per_page={limit}&sort=created&direction=desc",
             "--jq", ".[] | {name, full_name, html_url, stargazers_count, language, description, updated_at, topics}"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return [{"error": result.stderr.strip()}]
        # gh api outputs JSON lines, not a JSON array
        lines = [l.strip() for l in result.stdout.strip().split("\n") if l.strip()]
        repos = [json.loads(l) for l in lines]
        for r in repos:
            r["_scanned_at"] = datetime.now(timezone.utc).isoformat()
        return repos
    except Exception as e:
        return [{"error": str(e)}]


def scan_starred() -> dict:
    """Check starred repos — find newest stars we haven't cataloged."""
    repos = gh_starred(limit=50)
    output_file = OUTPUT_DIR / "starred.json"
    output_file.write_text(json.dumps(repos, indent=2))
    return {"mode": "starred", "count": len(repos), "file": str(output_file)}


def scan_trending(language: str = None, days: int = 7) -> dict:
    """Get trending repos from last N days."""
    date_filter = f"pushed:>={datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    query_parts = [date_filter, "stars:>10"]
    if language:
        query_parts.append(f"language:{language}")
    
    query = " ".join(query_parts)
    repos = gh_search(query, limit=15)

    lang_tag = language or "all"
    output_file = OUTPUT_DIR / f"trending_{lang_tag}_{datetime.now().strftime('%Y%m%d')}.json"
    output_file.write_text(json.dumps(repos, indent=2))
    return {"mode": "trending", "language": lang_tag, "count": len(repos), "file": str(output_file)}


def scan_builders() -> dict:
    """Scan for best builder/AI-agent repos across tracked categories."""
    all_results = {}
    for category, queries in TRACKED_CATEGORIES.items():
        cat_results = []
        for query in queries[:2]:  # Top 2 queries per category
            repos = gh_search(query, limit=5, sort="stars")
            cat_results.extend(repos)
        # Deduplicate by URL
        seen = set()
        unique = []
        for r in cat_results:
            url = r.get("url", "")
            if url and url not in seen:
                seen.add(url)
                unique.append(r)
        all_results[category] = unique

    output_file = OUTPUT_DIR / f"builders_{datetime.now().strftime('%Y%m%d')}.json"
    output_file.write_text(json.dumps(all_results, indent=2))
    total = sum(len(v) for v in all_results.values())
    return {"mode": "builders", "categories": len(all_results), "total_repos": total, "file": str(output_file)}


def scan_repo(repo_url: str) -> dict:
    """Deep-scan a specific repo."""
    # Use gh to get detailed info
    try:
        # Extract owner/repo from URL
        parts = repo_url.rstrip("/").split("/")
        owner, name = parts[-2], parts[-1]
        if "github.com" not in repo_url:
            return {"error": f"Not a GitHub URL: {repo_url}"}
        
        result = subprocess.run(
            ["gh", "repo", "view", f"{owner}/{name}",
             "--json", "name,owner,url,stargazersCount,language,description,updatedAt,createdAt,topics,licenseInfo,openIssuesTotal,watchersCount,forkCount,defaultBranchRef"],
            capture_output=True, text=True, timeout=30
        )
        if result.returncode != 0:
            return {"error": result.stderr.strip(), "repo": repo_url}
        
        repo = json.loads(result.stdout)
        
        # Also get README
        readme_result = subprocess.run(
            ["gh", "api", f"/repos/{owner}/{name}/readme",
             "--jq", ".content"],
            capture_output=True, text=True, timeout=30
        )
        if readme_result.returncode == 0 and readme_result.stdout.strip():
            import base64
            try:
                readme = base64.b64decode(readme_result.stdout.strip()).decode("utf-8")[:3000]
                repo["readme_preview"] = readme
            except:
                pass
        
        repo["_scanned_at"] = datetime.now(timezone.utc).isoformat()
        return repo
    except Exception as e:
        return {"error": str(e), "repo": repo_url}


def scan_categories() -> dict:
    """Full category scan — one query per category."""
    all_results = {}
    for category, queries in TRACKED_CATEGORIES.items():
        # Use the first query as representative
        repos = gh_search(queries[0], limit=5, sort="stars")
        all_results[category] = repos

    output_file = OUTPUT_DIR / f"categories_{datetime.now().strftime('%Y%m%d')}.json"
    output_file.write_text(json.dumps(all_results, indent=2))
    return {"mode": "categories", "categories": len(all_results), "file": str(output_file)}


def print_status():
    """Print current scout data status."""
    if not OUTPUT_DIR.exists():
        print("No scout data yet.")
        return
    
    files = sorted(OUTPUT_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"\nScout data files ({len(files)}):")
    for f in files[:10]:
        age = datetime.now().timestamp() - f.stat().st_mtime
        age_str = f"{age/3600:.1f}h ago" if age < 86400 else f"{age/86400:.1f}d ago"
        size_kb = f.stat().st_size / 1024
        print(f"  {f.name:50s} {size_kb:6.1f}KB  {age_str:>10s}")


# === MAIN ===
COMMANDS = {
    "starred": scan_starred,
    "trending": lambda: scan_trending(),
    "trending-python": lambda: scan_trending("Python"),
    "trending-typescript": lambda: scan_trending("TypeScript"),
    "builders": scan_builders,
    "categories": scan_categories,
    "status": print_status,
}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: github_scout.py <command> [args]")
        print(f"Commands: {', '.join(COMMANDS.keys())}")
        print("         repo <url>  — deep scan specific repo")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "repo" and len(sys.argv) > 2:
        result = scan_repo(sys.argv[2])
        print(json.dumps(result, indent=2))
    elif cmd in COMMANDS:
        result = COMMANDS[cmd]()
        print(json.dumps(result, indent=2, default=str))
    elif cmd == "all":
        results = {}
        for name, fn in COMMANDS.items():
            if name != "status" and not name.startswith("trending-"):
                try:
                    results[name] = fn()
                except Exception as e:
                    results[name] = {"error": str(e)}
        # Also do Python trending
        try:
            results["trending-python"] = scan_trending("Python")
        except:
            pass
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)
