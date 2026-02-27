import requests
import logging
import os
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

ADZUNA_APP_ID = os.getenv("ADZUNA_APP_ID")
ADZUNA_API_KEY = os.getenv("ADZUNA_API_KEY")

SEARCH_TERMS = [
    "software engineer",
    "data analyst",
    "python developer",
    "full stack developer",
    "machine learning",
]


def scrape_jobs():
    if ADZUNA_APP_ID and ADZUNA_API_KEY:
        jobs = scrape_adzuna()
        if jobs:
            return deduplicate_jobs(jobs)
    logger.warning("Adzuna credentials missing — using mock data")
    return get_mock_jobs()


def scrape_adzuna():
    all_jobs = []
    for term in SEARCH_TERMS:
        try:
            res = requests.get(
                "https://api.adzuna.com/v1/api/jobs/in/search/1",
                params={
                    "app_id": ADZUNA_APP_ID,
                    "app_key": ADZUNA_API_KEY,
                    "results_per_page": 5,
                    "what": term,
                    "where": "Hyderabad",
                },
                timeout=10,
            )
            res.raise_for_status()
            data = res.json()

            for item in data.get("results", []):
                sal_min = item.get("salary_min")
                sal_max = item.get("salary_max")
                if sal_min and sal_max:
                    salary = f"₹{int(sal_min):,} - ₹{int(sal_max):,}"
                elif sal_min:
                    salary = f"₹{int(sal_min):,}+"
                else:
                    salary = "Not disclosed"

                all_jobs.append({
                    "title": item.get("title", "Software Engineer"),
                    "company": item.get("company", {}).get("display_name", "Unknown"),
                    "location": item.get("location", {}).get("display_name", "Hyderabad"),
                    "skills": extract_skills(item.get("description", ""), term),
                    "type": "Full-time",
                    "salary": salary,
                    "url": item.get("redirect_url", "https://www.adzuna.in"),
                    "verified": True,
                    "source": "Adzuna",
                })

            logger.info(f"[Adzuna] '{term}' -> {len(data.get('results', []))} jobs")

        except Exception as e:
            logger.error(f"[Adzuna] Failed for '{term}': {e}")

    return all_jobs


def extract_skills(description, search_term):
    known_skills = [
        "Python", "Java", "JavaScript", "TypeScript", "React", "Node.js",
        "SQL", "MySQL", "PostgreSQL", "MongoDB", "AWS", "Azure", "GCP",
        "Docker", "Kubernetes", "Git", "Linux", "Machine Learning",
        "TensorFlow", "PyTorch", "Pandas", "NumPy", "Scikit-learn",
        "Power BI", "Tableau", "Excel", "C++", "C#", ".NET",
        "Spring Boot", "Flask", "Django", "Kafka", "Spark",
        "Terraform", "Jenkins", "HTML", "CSS", "Angular",
    ]
    desc_lower = description.lower()
    found = [s for s in known_skills if s.lower() in desc_lower]

    term_defaults = {
        "python developer": ["Python", "Flask", "Django"],
        "data analyst": ["SQL", "Excel", "Power BI", "Python"],
        "software engineer": ["Java", "Python", "SQL", "Git"],
        "full stack developer": ["React", "Node.js", "MongoDB", "JavaScript"],
        "machine learning": ["Python", "TensorFlow", "Scikit-learn", "NumPy"],
    }
    defaults = term_defaults.get(search_term, ["Python", "SQL"])
    return list(dict.fromkeys(found + defaults))[:6]


def deduplicate_jobs(jobs):
    seen = set()
    unique = []
    for job in jobs:
        key = (job.get("title", "").lower()[:30], job.get("company", "").lower())
        if key not in seen:
            seen.add(key)
            unique.append(job)
    return unique


def get_mock_jobs():
    return [
        {
            "title": "Software Engineer",
            "company": "TCS",
            "location": "Hyderabad",
            "skills": ["Java", "Spring Boot", "SQL", "Git"],
            "type": "Full-time",
            "salary": "₹3,50,000 - ₹7,00,000",
            "url": "https://www.tcs.com/careers/tcs-careers-apply-for-jobs",
            "verified": True,
            "source": "Mock",
        },
        {
            "title": "Data Scientist",
            "company": "Infosys",
            "location": "Hyderabad",
            "skills": ["Python", "Machine Learning", "TensorFlow", "SQL"],
            "type": "Full-time",
            "salary": "₹8,00,000 - ₹14,00,000",
            "url": "https://www.infosys.com/careers/apply-jobs.html",
            "verified": True,
            "source": "Mock",
        },
        {
            "title": "Full Stack Developer",
            "company": "Wipro",
            "location": "Hyderabad",
            "skills": ["React", "Node.js", "MongoDB", "TypeScript"],
            "type": "Full-time",
            "salary": "₹8,00,000 - ₹15,00,000",
            "url": "https://careers.wipro.com",
            "verified": True,
            "source": "Mock",
        },
        {
            "title": "DevOps Engineer",
            "company": "Tech Mahindra",
            "location": "Hyderabad",
            "skills": ["Docker", "Kubernetes", "AWS", "Jenkins"],
            "type": "Full-time",
            "salary": "₹9,00,000 - ₹16,00,000",
            "url": "https://careers.techmahindra.com",
            "verified": True,
            "source": "Mock",
        },
        {
            "title": "Python Developer Intern",
            "company": "Internshala",
            "location": "Hyderabad",
            "skills": ["Python", "Flask", "REST APIs", "Git"],
            "type": "Internship",
            "salary": "₹15,000 - ₹25,000/month",
            "url": "https://internshala.com/internships/python-internship",
            "verified": True,
            "source": "Mock",
        },
    ]