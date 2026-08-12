from candidate.services.resume_parser import parse_resume


if __name__ == "__main__":
    resume_path = "candidate/sample_resume.pdf"

    result = parse_resume(resume_path)

    print("\n========== PARSED RESUME ==========\n")

    print("Name:")
    print(result["name"])

    print("\nEmail:")
    print(result["email"])

    print("\nPhone:")
    print(result["phone"])

    print("\nSkills:")
    print(result["skills"])

    print("\nExperience:")
    print(result["experience"])

    print("\nProjects:")
    print(result["projects"])

    print("\nKeywords:")
    print(result["keywords"])

    print("\n========== EXTRACTED RESUME TEXT ==========")
    print(result["extracted_text"])
    print("===========================================")