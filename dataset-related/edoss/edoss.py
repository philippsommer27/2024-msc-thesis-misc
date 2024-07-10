from datetime import datetime, timezone
import os
import subprocess
import csv
import functools
import sys
import requests
import time

query = """
query($owner: String!, $name: String!) {
    repository(owner: $owner, name: $name) {
    primaryLanguage {
        name
    }
    defaultBranchRef {
        target {
        ... on Commit {
            history(first: 1) {
            edges {
                node {
                committedDate
                }
            }
            }
        }
        }
    }
    }
}
"""

checked = 0
total = 0

def read_edoss_file(file_path, out):
    global total
    columns = []
    with open(file_path) as tsv:
        for column in zip(*[line for line in csv.reader(tsv, dialect="excel-tab")]):
            columns.append(column)

    repos = columns[0]

    history_file = read_history_file(out)
    if history_file:
        print(f"Skipping {len(history_file)} already checked repositories...")
        repos = subtract_lists(repos, history_file)
    
    total = len(repos)

    return repos

def read_history_file(out):
    history_file = out + "/.history"
    try:
        with open(history_file) as f:
            return set({line.strip() for line in f})
    except FileNotFoundError:
        return None
    
def write_history_file(out, repo):
    history_file = out + "/.history"
    # Create the history file if it doesn't exist
    if not os.path.exists(history_file):
        with open(history_file, "w") as f:
            f.write(repo + "\n")
    else:
        with open(history_file, "a") as f:
            f.write(repo + "\n")
    
def subtract_lists(list1, set2):
    print(type(list1[0]))
    return [item for item in list1 if item not in set2]

def extract_name(repo_url):
    return "/".join(repo_url.split("/")[-2:])

def check_suitability(repo_url, age_limit, language, gh_token, out):
    name = extract_name(repo_url)
    global checked
    global total
    checked += 1
    print(f"### Checking {name} [{checked}/{total}]###")
    
    write_history_file(out, repo_url)

    owner, repo_name = name.split('/')
    variables = {
        "owner": owner,
        "name": repo_name
    }

    headers = {
        "Authorization": f"Bearer {gh_token}",
        "Content-Type": "application/json",
    }

    max_retries = 5
    retry_count = 0
    base_wait_time = 60  # 1 minute

    while retry_count < max_retries:
        try:
            response = requests.post(
                "https://api.github.com/graphql",
                json={"query": query, "variables": variables},
                headers=headers
            )
            
            if response.status_code == 429:  # Rate limit exceeded
                retry_after = response.headers.get('retry-after')
                if retry_after:
                    wait_time = int(retry_after)
                elif response.headers.get('x-ratelimit-remaining') == '0':
                    reset_time = int(response.headers.get('x-ratelimit-reset', 0))
                    wait_time = max(reset_time - int(time.time()), 0)
                else:
                    wait_time = base_wait_time * (2 ** retry_count)  # Exponential backoff
                
                print(f"Rate limit exceeded. Waiting for {wait_time} seconds before retrying.")
                time.sleep(wait_time)
                retry_count += 1
                continue

            response.raise_for_status()
            data = response.json()["data"]["repository"]

            if data is None:
                print(f"ERROR: Repository {name} not found or inaccessible")
                return False

            primary_language = data["primaryLanguage"]
            if primary_language is None:
                print("ERROR: No primary language, probably an empty or archived repo")
                return False

            primary_language_name = primary_language["name"]
            print(f"Primary language is {primary_language_name}")
            if primary_language_name != language:
                return False

            last_commit_date = data["defaultBranchRef"]["target"]["history"]["edges"][0]["node"]["committedDate"]
            last_commit_date = datetime.fromisoformat(last_commit_date.replace('Z', '+00:00'))
            now = datetime.now(timezone.utc)
            age = (now - last_commit_date).days
            print(f"Last commit was {age} days ago")

            return age < (age_limit * 365)

        except requests.exceptions.RequestException as e:
            print(f"Failed to fetch data for {name}: {e}")
            if retry_count < max_retries - 1:
                wait_time = base_wait_time * (2 ** retry_count)
                print(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
                retry_count += 1
            else:
                print("Max retries reached. Giving up.")
                return False

    print("Max retries reached. Giving up.")
    return False


def run(file_path, age_limit, language, gh_token, out):
    repos = read_edoss_file(file_path, out)
    is_suitable = functools.partial(check_suitability, age_limit=age_limit, language=language, gh_token=gh_token, out=out)
    filtered_repos = filter(is_suitable, repos)
    
    for repo in filtered_repos:
        clone_url = f"{repo}.git"
        print(f"Cloning {clone_url}")
        subprocess.run(['git', 'clone', clone_url], cwd=out)

if __name__ == "__main__":
    token = sys.argv[1]
    out = sys.argv[2]
    run("enterprise_projects.txt", 3, "Java", token, out)