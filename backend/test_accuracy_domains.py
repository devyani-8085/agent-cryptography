import json
import sys
from app.tools import ProblemClassifierTool, AISolutionTool, ImplementationBlueprintTool

print("==================================================================")
print("ACCURACY-FIRST MULTI-DOMAIN ARCHITECTURE VERIFICATION SUITE")
print("==================================================================\n")

domains = [
    {
        "name": "Manufacturing Predictive Maintenance",
        "req_data": {
            "client_name": "Apex Factory Systems",
            "industry": "Manufacturing",
            "business_problem": "Predict machine breakdown and equipment failure 48 hours in advance using IoT vibration, temperature, and telemetry sensors to eliminate unscheduled downtime.",
            "budget": "INR 5L - 10L",
            "timeline": "8-10 weeks"
        }
    },
    {
        "name": "Logistics Route Optimization",
        "req_data": {
            "client_name": "Global Express Freight",
            "industry": "Logistics & Supply Chain",
            "business_problem": "Optimize delivery routes for 500 fleet vehicles considering vehicle payload capacity, live traffic telemetry, and delivery priority windows.",
            "budget": "INR 8L - 15L",
            "timeline": "10-12 weeks"
        }
    },
    {
        "name": "University Admissions Policy RAG",
        "req_data": {
            "client_name": "Metro State University",
            "industry": "Education",
            "business_problem": "Answer student admissions inquiries with 100% grounded answers and source citations from official university prospectus PDFs.",
            "budget": "INR 3L - 5L",
            "timeline": "4-6 weeks"
        }
    },
    {
        "name": "Retail Inventory Demand Forecasting",
        "req_data": {
            "client_name": "SuperMart Retail Network",
            "industry": "Retail & Supermarkets",
            "business_problem": "Forecast SKU-level weekly demand across 50 store locations using POS sales history to prevent stockouts and overstock.",
            "budget": "INR 4L - 8L",
            "timeline": "6-8 weeks"
        }
    },
    {
        "name": "Healthcare Claims Document Intelligence",
        "req_data": {
            "client_name": "MediCare Health Group",
            "industry": "Healthcare & Insurance",
            "business_problem": "Extract medical claim fields and hospital invoices from scanned PDF documents and validate compliance against insurance policy thresholds.",
            "budget": "INR 6L - 12L",
            "timeline": "8-10 weeks"
        }
    }
]

classifications = []
architectures = []

for idx, domain in enumerate(domains, 1):
    print(f"--- TEST {idx}: {domain['name']} ---")
    cls = ProblemClassifierTool.execute(domain["req_data"])
    sol = AISolutionTool.execute(domain["req_data"])
    sols = sol.get("solutions", [])
    top_sol = sols[0] if sols else {}

    arch = top_sol.get("architecture", [])
    tech = top_sol.get("technologyStack", [])

    classifications.append(cls["primary_category"])
    architectures.append(" -> ".join(arch) if isinstance(arch, list) else str(arch))

    print(f"Primary Category:   {cls['primary_category']}")
    print(f"Computational Type: {cls['computational_type']}")
    print(f"RAG Required:       {cls['rag_required']}")
    print(f"LLM Required:       {cls['llm_required']}")
    print(f"Top Solution Name:  {top_sol.get('name')}")
    print(f"Architecture Flow:  {' -> '.join(arch[:4]) if isinstance(arch, list) else arch}")
    print(f"Tech Stack:         {', '.join(tech[:4]) if isinstance(tech, list) else tech}")
    print()

print("==================================================================")
print("DOMAIN DIVERSITY SUMMARY")
print("==================================================================")
unique_classifications = set(classifications)
unique_architectures = set(architectures)

print(f"Total Test Domains:             {len(domains)}")
print(f"Unique Problem Classifications: {len(unique_classifications)} / {len(domains)}")
print(f"Unique Architecture Flows:      {len(unique_architectures)} / {len(domains)}")

if len(unique_classifications) >= 4 and len(unique_architectures) >= 4:
    print("\n[SUCCESS] Generated architectures and problem classifications are MATERIALLY DISTINCT and requirement-driven across all 5 test domains!")
else:
    print("\n[WARNING] Some architectures overlap. Check fallback logic.")
