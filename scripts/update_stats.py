"""Write last-12-month GitHub stats into README.md between the STATS markers.

GitHub's contributionsCollection defaults to the past year up to now when no
from/to is given, i.e. the same rolling window as the profile contribution graph.
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

USER = os.environ["GH_USER"]
TOKEN = os.environ["GH_TOKEN"]
README = "README.md"

QUERY = """
query($login: String!) {
  user(login: $login) {
    contributionsCollection {
      contributionCalendar { totalContributions }
      totalCommitContributions
      totalPullRequestContributions
      totalIssueContributions
      totalPullRequestReviewContributions
      totalRepositoriesWithContributedCommits
    }
  }
}
"""


def fetch_stats() -> dict:
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": QUERY, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as resp:
        body = json.load(resp)
    if "errors" in body:
        sys.exit(f"GraphQL error: {body['errors']}")
    return body["data"]["user"]["contributionsCollection"]


def badge(label: str, value: int, color: str, logo: str | None = None) -> str:
    message = urllib.parse.quote(f"{value:,}")
    url = f"https://img.shields.io/badge/{label}-{message}-{color}?style=for-the-badge"
    if logo:
        url += f"&logo={logo}&logoColor=white"
    alt = label.replace("_", " ")
    return f'  <img alt="{alt}: {value:,}" src="{url}" />'


def build_block(c: dict) -> str:
    badges = [
        badge("Contributions", c["contributionCalendar"]["totalContributions"], "2EA043", "github"),
        badge("Commits", c["totalCommitContributions"], "1F6FEB", "git"),
        badge("Pull_Requests", c["totalPullRequestContributions"], "8957E5"),
        badge("Issues", c["totalIssueContributions"], "D29922"),
        badge("Reviews", c["totalPullRequestReviewContributions"], "BF4B8A"),
        badge("Repos_Contributed_To", c["totalRepositoriesWithContributedCommits"], "57606A"),
    ]
    return "\n".join(
        ["<p>", *badges, "</p>", "", "<sub>Last 12 months, same window as the contribution graph</sub>"]
    )


def main() -> None:
    with open(README, encoding="utf-8") as f:
        text = f.read()

    pattern = re.compile(r"(<!-- STATS:START -->\n).*?(\n<!-- STATS:END -->)", re.DOTALL)
    if not pattern.search(text):
        sys.exit("STATS markers not found in README.md")

    block = build_block(fetch_stats())
    new_text = pattern.sub(lambda m: m.group(1) + block + m.group(2), text)

    if new_text != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new_text)
        print("README stats updated")
    else:
        print("No change")


if __name__ == "__main__":
    main()