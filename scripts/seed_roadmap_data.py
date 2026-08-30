"""Regenerate data/prereqs.json and data/resources.json.

Both are hand-curated, which the README states plainly: a good curated map
beats a bad recommender, and the difference between "I learned this" and
"I encoded domain knowledge" is worth being precise about.

    python scripts/seed_roadmap_data.py
"""

from __future__ import annotations

import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

PREREQS = {
    "_note": (
        "Stage 4. skill_id -> skills to learn first. Hand-curated. Must stay a "
        "DAG; build_roadmap() fails loudly on a cycle rather than silently "
        "truncating the list."
    ),
    "fastapi": ["python"], "django": ["python"], "flask": ["python"],
    "pandas": ["python"], "numpy": ["python"], "matplotlib": ["python"],
    "scikit-learn": ["python", "numpy"], "pyspark": ["python"],
    "machine-learning": ["python", "statistics"], "nlp": ["machine-learning"],
    "spring": ["java"], "spring-boot": ["java", "spring"],
    "hibernate": ["java"], "jsp": ["java"], "struts": ["java"],
    "jdbc": ["java", "sql"], "maven": ["java"], "groovy": ["java"],
    "kotlin": ["java"], "android": ["kotlin"],
    "nodejs": ["javascript"], "express": ["nodejs"], "react": ["javascript"],
    "angular": ["javascript", "typescript"], "vue": ["javascript"],
    "jquery": ["javascript"], "redux": ["react"], "typescript": ["javascript"],
    "react-native": ["react"], "mean-stack": ["nodejs", "mongodb"],
    "ajax": ["javascript"], "dom": ["javascript"],
    "css": ["html"], "bootstrap": ["css"], "responsive-design": ["css"],
    "laravel": ["php"], "cakephp": ["php"], "smarty": ["php"],
    "wordpress": ["php"],
    "docker": ["linux"], "kubernetes": ["docker"], "shell": ["linux"],
    "ci-cd": ["git", "docker"], "devops": ["linux", "ci-cd"],
    "aws": ["cloud"], "azure": ["cloud"], "gcp": ["cloud"],
    "rest-api": ["json"], "graphql": ["rest-api"],
    "microservices": ["rest-api", "docker"], "kafka": ["microservices"],
    "system-design": ["rest-api", "database-design"],
    "design-patterns": ["oop"], "mvc": ["oop"], "flutter": ["oop"],
    "ios": ["oop"],
    "database-design": ["sql"], "mysql": ["sql"], "postgresql": ["sql"],
    "sql-server": ["sql"], "oracle-db": ["sql"], "sqlite": ["sql"],
    "stored-procedures": ["sql"], "query-optimization": ["sql", "database-design"],
    "nosql": ["database-design"], "mongodb": ["nosql"], "redis": ["nosql"],
    "cassandra": ["nosql"],
    "tableau": ["sql"], "power-bi": ["sql"], "business-intelligence": ["sql"],
    "data-visualization": ["excel"], "data-analysis": ["excel", "sql"],
    "etl": ["sql"], "bigquery": ["sql"], "redshift": ["sql"], "nifi": ["etl"],
    "testing": ["debugging"], "tdd": ["testing"], "selenium": ["testing"],
    "cypress": ["testing", "javascript"],
}


def r(title: str, url: str, kind: str, hours: int) -> dict:
    return {"title": title, "url": url, "kind": kind, "hours": hours}


RESOURCES = {
    "_note": (
        "Stage 4. Curated free resources per skill -- curated, NOT learned. A "
        "good hand-built map beats a bad recommender, and knowing the "
        "difference is the point. Free only; check links before shipping."
    ),
    "javascript": [r("JavaScript.info", "https://javascript.info/", "course", 40),
                   r("MDN JavaScript Guide", "https://developer.mozilla.org/en-US/docs/Web/JavaScript/Guide", "docs", 20)],
    "typescript": [r("TypeScript Handbook", "https://www.typescriptlang.org/docs/handbook/intro.html", "docs", 12)],
    "react": [r("React official tutorial", "https://react.dev/learn", "docs", 20)],
    "angular": [r("Angular Tutorials", "https://angular.dev/tutorials", "course", 20)],
    "vue": [r("Vue.js Guide", "https://vuejs.org/guide/introduction.html", "docs", 15)],
    "jquery": [r("jQuery Learning Center", "https://learn.jquery.com/", "docs", 8)],
    "html": [r("MDN HTML basics", "https://developer.mozilla.org/en-US/docs/Learn/HTML", "docs", 10)],
    "css": [r("MDN CSS basics", "https://developer.mozilla.org/en-US/docs/Learn/CSS", "docs", 15),
            r("Flexbox Froggy", "https://flexboxfroggy.com/", "practice", 2)],
    "bootstrap": [r("Bootstrap docs", "https://getbootstrap.com/docs/", "docs", 6)],
    "responsive-design": [r("MDN Responsive design", "https://developer.mozilla.org/en-US/docs/Learn/CSS/CSS_layout/Responsive_Design", "docs", 6)],
    "nodejs": [r("Node.js Getting Started", "https://nodejs.org/en/learn", "docs", 15)],
    "rest-api": [r("MDN HTTP overview", "https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview", "docs", 6),
                 r("REST API Tutorial", "https://restfulapi.net/", "docs", 5)],
    "json": [r("MDN Working with JSON", "https://developer.mozilla.org/en-US/docs/Learn/JavaScript/Objects/JSON", "docs", 2)],
    "python": [r("Automate the Boring Stuff", "https://automatetheboringstuff.com/", "book", 25),
               r("Official Python Tutorial", "https://docs.python.org/3/tutorial/", "docs", 12)],
    "java": [r("Java Tutorials", "https://dev.java/learn/", "docs", 30)],
    "spring-boot": [r("Spring Boot Guides", "https://spring.io/guides", "docs", 20)],
    "hibernate": [r("Hibernate Getting Started", "https://hibernate.org/orm/documentation/getting-started/", "docs", 10)],
    "sql": [r("SQLBolt", "https://sqlbolt.com/", "practice", 6),
            r("Mode SQL Tutorial", "https://mode.com/sql-tutorial/", "course", 10)],
    "mysql": [r("MySQL Tutorial", "https://dev.mysql.com/doc/refman/8.0/en/tutorial.html", "docs", 8)],
    "postgresql": [r("PostgreSQL Tutorial", "https://www.postgresqltutorial.com/", "course", 10)],
    "mongodb": [r("MongoDB University M001", "https://learn.mongodb.com/", "course", 12)],
    "nosql": [r("NoSQL explained", "https://www.mongodb.com/nosql-explained", "docs", 2)],
    "git": [r("Pro Git (free book)", "https://git-scm.com/book/en/v2", "book", 12),
            r("Learn Git Branching", "https://learngitbranching.js.org/", "practice", 4)],
    "docker": [r("Docker Get Started", "https://docs.docker.com/get-started/", "docs", 8)],
    "kubernetes": [r("Kubernetes Basics", "https://kubernetes.io/docs/tutorials/kubernetes-basics/", "docs", 12)],
    "ci-cd": [r("GitHub Actions quickstart", "https://docs.github.com/en/actions/quickstart", "docs", 5)],
    "linux": [r("Linux Journey", "https://linuxjourney.com/", "course", 12)],
    "shell": [r("Bash cheatsheet", "https://devhints.io/bash", "docs", 3)],
    "aws": [r("AWS Cloud Practitioner Essentials", "https://explore.skillbuilder.aws/", "course", 15)],
    "cloud": [r("What is cloud computing", "https://aws.amazon.com/what-is-cloud-computing/", "docs", 2)],
    "testing": [r("pytest docs", "https://docs.pytest.org/", "docs", 8),
                r("JUnit 5 User Guide", "https://junit.org/junit5/docs/current/user-guide/", "docs", 8)],
    "tdd": [r("Obey the Testing Goat", "https://www.obeythetestinggoat.com/", "book", 25)],
    "selenium": [r("Selenium docs", "https://www.selenium.dev/documentation/", "docs", 10)],
    "cypress": [r("Cypress docs", "https://docs.cypress.io/", "docs", 8)],
    "debugging": [r("Python pdb", "https://docs.python.org/3/library/pdb.html", "docs", 2)],
    "agile": [r("The Scrum Guide", "https://scrumguides.org/", "docs", 2)],
    "microservices": [r("Microservices patterns", "https://microservices.io/patterns/", "docs", 8)],
    "kafka": [r("Kafka Introduction", "https://kafka.apache.org/intro", "docs", 5)],
    "system-design": [r("System Design Primer", "https://github.com/donnemartin/system-design-primer", "book", 30)],
    "design-patterns": [r("Refactoring Guru: Design Patterns", "https://refactoring.guru/design-patterns", "docs", 15)],
    "oop": [r("Refactoring Guru: OOP basics", "https://refactoring.guru/design-patterns/what-is-pattern", "docs", 6)],
    "dsa": [r("NeetCode 150", "https://neetcode.io/practice", "practice", 80)],
    "excel": [r("Excel Easy", "https://www.excel-easy.com/", "course", 10)],
    "power-bi": [r("Microsoft Learn: Power BI", "https://learn.microsoft.com/en-us/training/powerplatform/power-bi", "course", 12)],
    "tableau": [r("Tableau free training", "https://www.tableau.com/learn/training/", "video", 10)],
    "statistics": [r("Khan Academy Statistics", "https://www.khanacademy.org/math/statistics-probability", "course", 25)],
    "data-visualization": [r("Matplotlib tutorials", "https://matplotlib.org/stable/tutorials/", "docs", 8)],
    "pandas": [r("10 minutes to pandas", "https://pandas.pydata.org/docs/user_guide/10min.html", "docs", 4)],
    "r": [r("R for Data Science", "https://r4ds.hadley.nz/", "book", 30)],
    "dotnet": [r("Microsoft Learn: C# and .NET", "https://learn.microsoft.com/en-us/dotnet/csharp/", "docs", 25)],
    "cpp": [r("learncpp.com", "https://www.learncpp.com/", "course", 50)],
    "php": [r("PHP The Right Way", "https://phptherightway.com/", "docs", 15)],
    "kotlin": [r("Kotlin Docs", "https://kotlinlang.org/docs/getting-started.html", "docs", 15)],
    "android": [r("Android Basics with Compose", "https://developer.android.com/courses", "course", 40)],
    "etl": [r("Airflow tutorial", "https://airflow.apache.org/docs/apache-airflow/stable/tutorial/", "docs", 10)],
}


def main() -> None:
    (DATA / "prereqs.json").write_text(
        json.dumps(PREREQS, indent=2) + "\n", encoding="utf-8")
    (DATA / "resources.json").write_text(
        json.dumps(RESOURCES, indent=2) + "\n", encoding="utf-8")
    print(f"prereqs   : {len(PREREQS) - 1} skills with dependencies")
    print(f"resources : {len(RESOURCES) - 1} skills covered")


if __name__ == "__main__":
    main()
