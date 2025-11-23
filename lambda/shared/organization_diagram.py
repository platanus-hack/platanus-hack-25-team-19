"""
Organization Diagram - Company Personnel and Project Registry

This module contains the organizational structure with personnel information
and their associated projects. Used by the orchestrator to match problems
with the right internal contacts for consultation.
"""

from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Project:
    """Represents a project that a person has worked on or is working on."""
    name: str
    description: str


@dataclass
class Person:
    """Represents a person in the organization with their role and projects."""
    name: str
    email: str
    role: str
    role_description: str
    projects: List[Project]


# --- ORGANIZATION PERSONNEL DATA ---

ORGANIZATION_PEOPLE: List[Person] = [
    # --- LEADERSHIP & STRATEGY ---
    Person(
        name="Maria Rodriguez",
        email="admin@welcomeback.io",
        role="CEO",
        role_description="Chief Executive Officer responsible for overall company strategy, vision, and major business decisions",
        projects=[
            Project("Digital Transformation Initiative", "Led company-wide digital transformation including cloud migration and process automation"),
            Project("Market Expansion Strategy", "Developed strategy for entering South American markets"),
            Project("Strategic Partnership Program", "Established key partnerships with major technology vendors")
        ]
    ),

    Person(
        name="Carlos Mendez",
        email="admin@welcomeback.io",
        role="CFO",
        role_description="Chief Financial Officer managing financial planning, budgeting, and investment decisions",
        projects=[
            Project("Financial Restructuring", "Led financial restructuring to improve cash flow and profitability"),
            Project("Cost Optimization Program", "Implemented cost reduction strategies saving 15% annually"),
            Project("Investment Analysis Framework", "Created framework for evaluating new business investments")
        ]
    ),

    # --- TECHNOLOGY & ENGINEERING ---
    Person(
        name="Ana Silva",
        email="jdlarrain@copec.cl",
        role="CTO",
        role_description="Chief Technology Officer overseeing technology strategy, architecture, and engineering teams",
        projects=[
            Project("Cloud Infrastructure Migration", "Migrated legacy systems to AWS with 99.9% uptime"),
            Project("AI Integration Platform", "Built ML platform for predictive analytics across business units"),
            Project("Cybersecurity Enhancement", "Implemented zero-trust security architecture")
        ]
    ),

    Person(
        name="Diego Fernandez",
        email="nhorellana@copec.cl",
        role="Senior Software Engineer",
        role_description="Lead developer specializing in backend systems, APIs, and database architecture",
        projects=[
            Project("Microservices Architecture", "Designed and implemented microservices replacing monolithic system"),
            Project("API Gateway Implementation", "Built scalable API gateway handling 10M+ requests daily"),
            Project("Database Performance Optimization", "Optimized database queries reducing response time by 60%")
        ]
    ),

    Person(
        name="Laura Kim",
        email="jtgonzalez@copec.cl",
        role="DevOps Engineer",
        role_description="DevOps specialist managing CI/CD pipelines, infrastructure automation, and monitoring",
        projects=[
            Project("CI/CD Pipeline Automation", "Automated deployment pipeline reducing deployment time by 80%"),
            Project("Infrastructure as Code", "Implemented Terraform for infrastructure management"),
            Project("Monitoring & Alerting System", "Built comprehensive monitoring with Prometheus and Grafana")
        ]
    ),

    # --- PRODUCT & DESIGN ---
    Person(
        name="Sofia Martinez",
        email="jschenke@copec.cl",
        role="Product Manager",
        role_description="Product manager responsible for product strategy, roadmap, and user experience",
        projects=[
            Project("Mobile App Redesign", "Led redesign of mobile app increasing user engagement by 40%"),
            Project("Customer Journey Optimization", "Analyzed and optimized customer journey reducing churn by 25%"),
            Project("Product Analytics Platform", "Implemented analytics to track product KPIs and user behavior")
        ]
    ),

    Person(
        name="Roberto Chen",
        email="jdlarrain@copec.cl",
        role="UX/UI Designer",
        role_description="User experience and interface designer focusing on user-centered design and accessibility",
        projects=[
            Project("Design System Creation", "Created comprehensive design system used across all products"),
            Project("Accessibility Compliance", "Ensured WCAG 2.1 AA compliance across all digital properties"),
            Project("User Research Program", "Established user research program with quarterly usability studies")
        ]
    ),

    # --- SALES & MARKETING ---
    Person(
        name="Isabella Torres",
        email="nhorellana@copec.cl",
        role="Sales Director",
        role_description="Sales director managing enterprise sales, client relationships, and revenue growth",
        projects=[
            Project("Enterprise Sales Strategy", "Developed B2B sales strategy increasing enterprise revenue by 200%"),
            Project("CRM Implementation", "Implemented Salesforce CRM improving sales process efficiency"),
            Project("Customer Success Program", "Built customer success program reducing churn by 30%")
        ]
    ),

    Person(
        name="Miguel Gonzalez",
        email="jtgonzalez@copec.cl",
        role="Marketing Manager",
        role_description="Marketing manager specializing in digital marketing, content strategy, and brand management",
        projects=[
            Project("Digital Marketing Campaign", "Led campaign generating 500% increase in qualified leads"),
            Project("Content Marketing Strategy", "Developed content strategy increasing organic traffic by 300%"),
            Project("Brand Repositioning", "Managed brand refresh and repositioning in target markets")
        ]
    ),

    # --- OPERATIONS & FINANCE ---
    Person(
        name="Gabriela Lopez",
        email="jschenke@copec.cl",
        role="Operations Manager",
        role_description="Operations manager overseeing daily operations, process improvement, and efficiency optimization",
        projects=[
            Project("Process Automation Initiative", "Automated manual processes saving 200 hours monthly"),
            Project("Supply Chain Optimization", "Optimized supply chain reducing costs by 18%"),
            Project("Quality Management System", "Implemented ISO 9001 quality management system")
        ]
    ),

    Person(
        name="Fernando Ruiz",
        email="jdlarrain@copec.cl",
        role="Financial Analyst",
        role_description="Financial analyst specializing in financial modeling, budgeting, and business intelligence",
        projects=[
            Project("Financial Forecasting Model", "Built predictive model for revenue forecasting with 95% accuracy"),
            Project("Budget Management System", "Developed automated budgeting system for all departments"),
            Project("Business Intelligence Dashboard", "Created executive dashboard for real-time financial metrics")
        ]
    ),

    # --- HUMAN RESOURCES & LEGAL ---
    Person(
        name="Carmen Jimenez",
        email="nhorellana@copec.cl",
        role="HR Director",
        role_description="HR director managing talent acquisition, employee development, and organizational culture",
        projects=[
            Project("Remote Work Policy", "Developed comprehensive remote work policy and guidelines"),
            Project("Employee Development Program", "Created learning and development program with 95% satisfaction"),
            Project("Diversity & Inclusion Initiative", "Led D&I initiative increasing diverse hiring by 40%")
        ]
    ),

    Person(
        name="Alejandro Vega",
        email="jtgonzalez@copec.cl",
        role="Legal Counsel",
        role_description="Legal counsel handling contracts, compliance, intellectual property, and regulatory matters",
        projects=[
            Project("GDPR Compliance Program", "Ensured full GDPR compliance across all data processing activities"),
            Project("Contract Management System", "Implemented legal tech solution for contract lifecycle management"),
            Project("IP Portfolio Management", "Managed patent and trademark portfolio expansion")
        ]
    ),

    # --- CUSTOMER SUPPORT & SUCCESS ---
    Person(
        name="Natalia Morales",
        email="jschenke@copec.cl",
        role="Customer Support Manager",
        role_description="Customer support manager ensuring excellent customer service and satisfaction",
        projects=[
            Project("Customer Support Portal", "Built self-service portal reducing support tickets by 40%"),
            Project("24/7 Support Implementation", "Established round-the-clock customer support coverage"),
            Project("Customer Satisfaction Program", "Implemented NPS program achieving 8.5/10 average score")
        ]
    ),

    # --- DATA & ANALYTICS ---
    Person(
        name="Ricardo Soto",
        email="jdlarrain@copec.cl",
        role="Data Scientist",
        role_description="Data scientist specializing in machine learning, predictive analytics, and business intelligence",
        projects=[
            Project("Customer Churn Prediction", "Built ML model predicting customer churn with 87% accuracy"),
            Project("Recommendation Engine", "Developed product recommendation system increasing sales by 22%"),
            Project("Data Warehouse Architecture", "Designed and implemented data warehouse for business analytics")
        ]
    ),

    # --- INDUSTRY SPECIALISTS ---
    Person(
        name="Gonzalo Cortéz",
        email="jschenke@uc.cl",
        role="Salmon Industry Expert",
        role_description="Expert in salmon farming with extensive industry experience and participation in energy projects",
        projects=[
            Project("Sustainable Aquaculture Initiative", "Led sustainability program for salmon farming operations reducing environmental impact by 30%"),
            Project("Energy Efficiency in Salmon Farms", "Implemented renewable energy solutions in salmon farming facilities"),
            Project("Aquaculture Technology Innovation", "Developed IoT monitoring systems for water quality management")
        ]
    )
]


def get_organization_data() -> List[Dict[str, Any]]:
    """
    Returns the organization data as a list of dictionaries.
    Useful for JSON serialization and API responses.
    """
    return [
        {
            "name": person.name,
            "email": person.email,
            "role": person.role,
            "role_description": person.role_description,
            "projects": [
                {
                    "name": project.name,
                    "description": project.description
                }
                for project in person.projects
            ]
        }
        for person in ORGANIZATION_PEOPLE
    ]


def get_people_by_role(role: str) -> List[Person]:
    """Get all people with a specific role."""
    return [person for person in ORGANIZATION_PEOPLE if person.role.lower() == role.lower()]


def find_people_by_expertise(keywords: List[str]) -> List[Person]:
    """
    Find people whose projects or role descriptions contain specific keywords.
    Useful for matching problems to the right consultants.
    """
    results = []
    keywords_lower = [keyword.lower() for keyword in keywords]

    for person in ORGANIZATION_PEOPLE:
        # Check role description
        role_match = any(keyword in person.role_description.lower() for keyword in keywords_lower)

        # Check project descriptions
        project_match = any(
            keyword in project.description.lower() or keyword in project.name.lower()
            for project in person.projects
            for keyword in keywords_lower
        )

        if role_match or project_match:
            results.append(person)

    return results


def get_organization_summary() -> Dict[str, Any]:
    """Get a summary of the organization structure."""
    roles = {}
    total_projects = 0

    for person in ORGANIZATION_PEOPLE:
        if person.role not in roles:
            roles[person.role] = 0
        roles[person.role] += 1
        total_projects += len(person.projects)

    return {
        "total_people": len(ORGANIZATION_PEOPLE),
        "total_projects": total_projects,
        "roles_distribution": roles,
        "departments": list(set(person.role for person in ORGANIZATION_PEOPLE))
    }


if __name__ == "__main__":
    # Example usage
    print("=== ORGANIZATION SUMMARY ===")
    summary = get_organization_summary()
    print(f"Total People: {summary['total_people']}")
    print(f"Total Projects: {summary['total_projects']}")
    print(f"Roles: {', '.join(summary['roles_distribution'].keys())}")

    print("\n=== SAMPLE EXPERTISE SEARCH ===")
    ai_experts = find_people_by_expertise(["AI", "machine learning", "analytics"])
    print(f"AI/ML Experts ({len(ai_experts)}):")
    for expert in ai_experts:
        print(f"  - {expert.name} ({expert.role})")

    cloud_experts = find_people_by_expertise(["cloud", "AWS", "infrastructure"])
    print(f"\nCloud Experts ({len(cloud_experts)}):")
    for expert in cloud_experts:
        print(f"  - {expert.name} ({expert.role})")
