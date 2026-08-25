import os
import requests
from xml.sax.saxutils import escape

USERNAME = "vbrprabhu2004"

API = "https://api.github.com"

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2026-03-10",
}

# GitHub language colors
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
    """Get all public repositories owned by the user."""

    repositories = []
    page = 1

    while True:
        url = f"{API}/users/{USERNAME}/repos"

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


def get_languages(repository):
    """Get GitHub's language byte counts for a repository."""

    owner = repository["owner"]["login"]
    name = repository["name"]

    url = f"{API}/repos/{owner}/{name}/languages"

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

    print(f"Found {len(repositories)} public repositories.")

    for repository in repositories:

        # Ignore forks.
        if repository.get("fork"):
            print(f"Skipping fork: {repository['name']}")
            continue

        # Ignore archived repositories.
        if repository.get("archived"):
            print(f"Skipping archived repository: {repository['name']}")
            continue

        name = repository["name"]

        print(f"Processing: {name}")

        languages = get_languages(repository)

        for language, byte_count in languages.items():

            totals[language] = (
                totals.get(language, 0) + byte_count
            )

    return totals


def create_svg(languages):

    total_bytes = sum(languages.values())

    if total_bytes == 0:
        raise RuntimeError(
            "No programming language data was found."
        )

    sorted_languages = sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True,
    )

    # Show maximum 10 languages.
    MAX_LANGUAGES = 10

    if len(sorted_languages) > MAX_LANGUAGES:

        visible = sorted_languages[:MAX_LANGUAGES]

        other_bytes = sum(
            value
            for _, value in sorted_languages[MAX_LANGUAGES:]
        )

        visible.append(("Other", other_bytes))

    else:
        visible = sorted_languages

    percentages = []

    for language, byte_count in visible:

        percentage = (
            byte_count / total_bytes
        ) * 100

        percentages.append(
            (language, byte_count, percentage)
        )

    # --------------------------------------------------
    # Dynamic SVG dimensions
    # --------------------------------------------------

    width = 900

    # Two legend columns
    columns = 2

    # Calculate number of rows required
    rows = (len(percentages) + columns - 1) // columns

    # Dynamic height based on number of languages
    title_height = 65
    bar_height = 55
    legend_top = 125
    row_height = 38
    bottom_padding = 25

    height = (
        title_height
        + bar_height
        + (rows * row_height)
        + bottom_padding
    )

    bar_x = 40
    bar_y = 62
    bar_width = 820
    language_bar_height = 32

    svg = []

    svg.append(
    f'''<svg xmlns="http://www.w3.org/2000/svg"
width="{width}"
height="{height}"
viewBox="0 0 {width} {height}">

<rect
width="100%"
height="100%"
rx="12"
fill="#ffffff"/>

<style>

.title {{
    font: 700 24px -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
    fill: #24292f;
}}

.language {{
    font: 600 15px -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
    fill: #24292f;
}}

.percentage {{
    font: 400 14px -apple-system,
    BlinkMacSystemFont,
    "Segoe UI",
    sans-serif;
    fill: #57606a;
}}

</style>

<text
x="40"
y="40"
class="title">
VBRP's GitHub Profile – Language Composition
</text>
'''
    )

    # --------------------------------------------------
    # Stacked language bar
    # --------------------------------------------------

    current_x = bar_x

    for language, byte_count, percentage in percentages:

        segment_width = (
            bar_width * percentage / 100
        )

        color = COLORS.get(
            language,
            "#8b949e"
        )

        svg.append(
            f'''
<rect
x="{current_x:.2f}"
y="{bar_y}"
width="{segment_width:.2f}"
height="{language_bar_height}"
fill="{color}"/>
'''
        )

        current_x += segment_width

    # --------------------------------------------------
    # Dynamic legend
    # --------------------------------------------------

    legend_y = legend_top
    column_width = 410

    for index, (
        language,
        byte_count,
        percentage
    ) in enumerate(percentages):

        column = index % columns
        row = index // columns

        x = 40 + column * column_width
        y = legend_y + row * row_height

        color = COLORS.get(
            language,
            "#8b949e"
        )

        svg.append(
            f'''
<circle
cx="{x}"
cy="{y - 5}"
r="6"
fill="{color}"/>

<text
x="{x + 16}"
y="{y}"
class="language">
{escape(language)}
</text>

<text
x="{x + 160}"
y="{y}"
class="percentage">
{percentage:.2f}%
</text>
'''
        )

    svg.append("</svg>")

    return "\n".join(svg)

def main():

    languages = calculate_languages()

    total = sum(languages.values())

    print("\n==============================")
    print("VBRP's GitHub Profile – Language Composition")
    print("==============================")

    for language, byte_count in sorted(
        languages.items(),
        key=lambda item: item[1],
        reverse=True
    ):

        percentage = (
            byte_count / total
        ) * 100

        print(
            f"{language}: "
            f"{percentage:.2f}% "
            f"({byte_count:,} bytes)"
        )

    svg = create_svg(languages)

    os.makedirs(
        "assets",
        exist_ok=True
    )

    with open(
        "assets/github-languages.svg",
        "w",
        encoding="utf-8"
    ) as file:

        file.write(svg)

    print(
        "\nGenerated "
        "assets/github-languages.svg"
    )


if __name__ == "__main__":
    main()
