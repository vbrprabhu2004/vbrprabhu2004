import os
import requests
from xml.sax.saxutils import escape

USERNAME = "vbrprabhu2004"
TOKEN = os.environ.get("GITHUB_TOKEN")

API = "https://api.github.com"
HEADERS = {
    "Accept": "application/vnd.github+json",
    "Authorization": f"Bearer {TOKEN}",
    "X-GitHub-Api-Version": "2026-03-10",
}

# Common GitHub language colors
COLORS = {
    "Python": "#3572A5",
    "Java": "#b07219",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "C": "#555555",
    "C++": "#f34b7d",
    "C#": "#178600",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Kotlin": "#A97BFF",
    "Swift": "#F05138",
    "Dart": "#00B4AB",
    "HTML": "#e34c26",
    "CSS": "#563d7c",
    "Shell": "#89e051",
    "Jupyter Notebook": "#DA5B0B",
    "SQL": "#e38c00",
    "PHP": "#4F5D95",
    "Ruby": "#701516",
    "Vue": "#41b883",
}


def get_repositories():
    repositories = []
    page = 1

    while True:
        url = f"{API}/user/repos"
        params = {
            "type": "owner",
            "per_page": 100,
            "page": page,
        }

        response = requests.get(
            url,
            headers=HEADERS,
            params=params,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        if not data:
            break

        repositories.extend(data)

        if len(data) < 100:
            break

        page += 1

    return repositories


def get_languages(owner, repo):
    url = f"{API}/repos/{owner}/{repo}/languages"

    response = requests.get(
        url,
        headers=HEADERS,
        timeout=30,
    )

    if response.status_code == 404:
        return {}

    response.raise_for_status()
    return response.json()


def calculate_languages():
    totals = {}

    repositories = get_repositories()

    for repo in repositories:

        # Ignore forks because their code is not originally yours.
        if repo.get("fork"):
            continue

        # Ignore archived repositories.
        if repo.get("archived"):
            continue

        repo_name = repo["name"]

        print(f"Processing: {repo_name}")

        languages = get_languages(USERNAME, repo_name)

        for language, bytes_count in languages.items():
            totals[language] = totals.get(language, 0) + bytes_count

    return totals


def create_svg(languages):
    total_bytes = sum(languages.values())

    if total_bytes == 0:
        raise RuntimeError("No language data found.")

    # Sort by byte count
    sorted_languages = sorted(
        languages.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    # Keep the largest 10 languages visible.
    # Everything else is combined into Other.
    MAX_LANGUAGES = 10

    if len(sorted_languages) > MAX_LANGUAGES:
        visible = sorted_languages[:MAX_LANGUAGES]
        other_bytes = sum(
            value for _, value in sorted_languages[MAX_LANGUAGES:]
        )
        visible.append(("Other", other_bytes))
    else:
        visible = sorted_languages

    percentages = [
        (language, value, value / total_bytes * 100)
        for language, value in visible
    ]

    width = 900
    height = 360

    bar_x = 40
    bar_y = 85
    bar_width = 820
    bar_height = 32

    svg = []

    svg.append(
        f'''<svg xmlns="http://www.w3.org/2000/svg"
        width="{width}"
        height="{height}"
        viewBox="0 0 {width} {height}">
        <rect width="100%" height="100%" rx="12"
        fill="#0d1117"/>
        
        <style>
            .title {{
                font: 700 24px -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
                fill: #ffffff;
            }}

            .language {{
                font: 600 15px -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
                fill: #ffffff;
            }}

            .percentage {{
                font: 400 14px -apple-system, BlinkMacSystemFont,
                "Segoe UI", sans-serif;
                fill: #8b949e;
            }}
        </style>

        <text x="40" y="45" class="title">
            GitHub Language Composition
        </text>
        '''
    )

    # Stacked language bar
    current_x = bar_x

    for language, value, percentage in percentages:

        segment_width = bar_width * (percentage / 100)

        color = COLORS.get(language, "#8b949e")

        svg.append(
            f'''
            <rect
                x="{current_x:.2f}"
                y="{bar_y}"
                width="{segment_width:.2f}"
                height="{bar_height}"
                fill="{color}"
            />
            '''
        )

        current_x += segment_width

    # Legend
    legend_y = 155

    columns = 2
    column_width = 410

    for index, (language, value, percentage) in enumerate(percentages):

        column = index % columns
        row = index // columns

        x = 40 + column * column_width
        y = legend_y + row * 38

        color = COLORS.get(language, "#8b949e")

        svg.append(
            f'''
            <circle
                cx="{x}"
                cy="{y - 5}"
                r="6"
                fill="{color}"
            />

            <text
                x="{x + 16}"
                y="{y}"
                class="language"
            >
                {escape(language)}
            </text>

            <text
                x="{x + 160}"
                y="{y}"
                class="percentage"
            >
                {percentage:.2f}%
            </text>
            '''
        )

    svg.append("</svg>")

    return "\n".join(svg)


def main():
    languages = calculate_languages()

    print("\nLanguage composition:")

    total = sum(languages.values())

    for language, value in sorted(
        languages.items(),
        key=lambda x: x[1],
        reverse=True,
    ):
        percentage = value / total * 100
        print(f"{language}: {percentage:.2f}%")

    svg = create_svg(languages)

    os.makedirs("assets", exist_ok=True)

    with open(
        "assets/github-languages.svg",
        "w",
        encoding="utf-8",
    ) as file:
        file.write(svg)

    print("\nGenerated: assets/github-languages.svg")


if __name__ == "__main__":
    main()
