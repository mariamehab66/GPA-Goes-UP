from chatbot.rag_engine import retrieve_relevant_rules


def build_prompt(
    student_data: dict,
    enrollment_history: list,
    rule_engine_result: dict | None,
    student_insights: dict,
    user_message: str,
    ml_result: dict | None = None,
    language: str = "auto",
    page_context: str = "",
) -> str:

    has_arabic = any("\u0600" <= c <= "\u06ff" for c in user_message)

    if language == "auto":
        lang_instruction = "Respond in Arabic." if has_arabic else "Respond in English."
    elif language == "arabic":
        lang_instruction = "Respond in Arabic."
        has_arabic = True
    else:
        lang_instruction = "Respond in English."
        has_arabic = False

    refusal = (
        "\u0639\u0630\u0631\u064b\u0627\u060c \u0623\u0646\u0627 \u0645\u062a\u062e\u0635\u0635 "
        "\u0641\u0642\u0637 \u0644\u0644\u0625\u0631\u0634\u0627\u062f \u0627\u0644\u0623\u0643"
        "\u0627\u062f\u064a\u0645\u064a. \u0643\u064a\u0641 \u064a\u0645\u0643\u0646\u0646\u064a "
        "\u0645\u0633\u0627\u0639\u062f\u062a\u0643\u061f"
        if has_arabic else
        "Sorry, I'm only here to help with academic advising for this program. "
        "What can I help you with regarding your studies?"
    )

    if enrollment_history:
        lines = []
        for e in enrollment_history:
            lines.append(
                f"  {e.get('Course_Code','?'):12} | "
                f"Grade: {e.get('Grade','?'):4} | "
                f"Marks: {e.get('Marks','?'):6} | "
                f"GPA Pts: {e.get('Course_GPA','?')} | "
                f"{e.get('Semester','?')} {e.get('Year','?')}"
            )
        history_text = "\n".join(lines)
    else:
        history_text = "No enrollment history available."

    if rule_engine_result:
        suggested = rule_engine_result.get("engine_suggested_courses", [])
        target_semester = str( rule_engine_result.get( "target_semester", "" ) ).lower() 
        eligible = [ c for c in rule_engine_result.get( "all_eligible_courses", [] ) 
                    if str( c.get("Semester", "") ).lower() == target_semester ][:10]
        warnings  = rule_engine_result.get("warnings", [])
        suggested_text = "\n".join(
            f"  - {c.get('Code')} | {c.get('Course_Name')} | "
            f"{c.get('Credit_Hours')} cr | Level {c.get('Level')} | "
            f"{'Elective' if c.get('Is_elective') else 'Core (required)'} | "
            f"{'FAILED BEFORE - retake' if c.get('is_failed') else 'Not yet taken'}"
            for c in suggested
        ) or "  None"
        eligible_text = "\n".join(
            f"  - {c.get('Code')} | {c.get('Course_Name')} | "
            f"{c.get('Credit_Hours')} cr | Level {c.get('Level')} | "
            f"Sem: {c.get('Semester')} | "
            f"{'Elective' if c.get('Is_elective') else 'Core (required)'} | "
            f"{'FAILED - retake needed' if c.get('is_failed') else 'Not yet taken'}"
            for c in eligible
        ) or "  None"
        rule_summary = (
            f"Academic Status: {rule_engine_result.get('academic_status')}\n"
            f"Max Allowed Hours: {rule_engine_result.get('max_allowed_hours')}\n"
            f"Target Semester: {rule_engine_result.get('target_semester')}\n"
            f"Warnings: {', '.join(warnings) if warnings else 'None'}\n\n"
            f"Rule Engine Top Suggestions:\n{suggested_text}\n\n"
            f"Eligible Courses For This Semester:\n{eligible_text}"
        )
    else:
        rule_summary = "Rule engine results not available."

    if ml_result:
        top = ml_result.get("top_recommended", [])
        alt = ml_result.get("alternative_courses", [])
        top_text = ""
        for c in top:
            probs = c.get("grade_probabilities", {})
            prob_str = " | ".join(
                f"{k}: {round(v*100,1)}%" for k, v in probs.items()
            )
            top_text += (
                f"\n  {c.get('Code')} | {c.get('Course_Name')}"
                f"\n    Expected difficulty: {c.get('predicted_grade_range')} ({c.get('predicted_grade_bucket')})"
                f"\n    Observed performance distribution for similar academic profiles: {prob_str}"
                f"\n    Credits: {c.get('Credit_Hours')}"
                f"\n    Type: {'Elective' if c.get('Is_elective') else 'Core required course'}"
            )
        alt_text = "\n".join(
            f"  - {c.get('Code')} | {c.get('Course_Name')}" for c in alt
        ) or "  None"
        ml_summary = (
            f"Total Recommended Hours: {ml_result.get('total_recommended_hours')}\n\n"
            f"ML Top Recommended:\n{top_text or '  None'}\n\n"
            f"ML Alternative Courses:\n{alt_text}"
        )
    else:
        ml_summary = "ML results not available."

    insights_text = (
        f"Risk Level: {student_insights.get('risk_level', 'unknown')}\n"
        f"Active Failed Courses: {', '.join(student_insights.get('active_failed_courses', [])) or 'None'}\n"
        f"Recovered Courses: {', '.join(student_insights.get('recovered_courses', [])) or 'None'}\n"
        f"Repeated Courses: {', '.join(student_insights.get('repeated_courses', [])) or 'None'}"
    )

    rag_results = retrieve_relevant_rules(user_message)
    rag_text = "\n\n".join(
        f"[{r['category']}]\nEN: {r['english']}\nAR: {r['arabic']}"
        for r in rag_results
    ) if rag_results else "No specific rules retrieved."

    course_topics = {
        "MATH 101": "Differential and Integral Calculus. Topics: limits, derivatives, integrals, applications.",
        "MATH 102": "Calculus 2. Topics: sequences, series, multivariable calculus.",
        "MATH 104": "Foundations of Mathematics. Topics: logic, sets, proofs, linear algebra basics.",
        "PHYS 101": "Physics 1. Topics: mechanics, motion, forces, energy, waves.",
        "CHEM 101": "General Chemistry. Topics: atomic structure, bonding, reactions, stoichiometry.",
        "STAT 101": "Introduction to Statistics. Topics: descriptive stats, probability basics, distributions.",
        "STAT 102": "Probability Theory 1. Topics: probability rules, random variables, distributions.",
        "STAT 201": "Statistical Theory 1. Topics: estimation, hypothesis testing, confidence intervals.",
        "STAT 202": "Statistical Theory 2. Topics: regression, ANOVA, advanced inference.",
        "STAT 203": "Statistical Methods 1. Topics: nonparametric tests, correlation, regression.",
        "STAT 204": "Probabilistic Operations Research 1. Topics: Markov chains, queuing, simulation.",
        "STAT 205": "Statistical Mathematics. Topics: probability theory, generating functions, transforms.",
        "STAT 301": "Statistical Inference 1. Topics: point estimation, interval estimation, testing.",
        "STAT 302": "Statistical Inference 2. Topics: advanced testing, decision theory.",
        "STAT 303": "Stochastic Processes 1. Topics: Markov chains, Poisson processes, random walks.",
        "STAT 304": "Sampling Methods. Topics: sampling designs, stratified, cluster, systematic sampling.",
        "STAT 305": "Order Statistics. Topics: extreme values, ranked data, nonparametric methods.",
        "STAT 405": "Design and Analysis of Experiments. Topics: experimental design, ANOVA, factorial designs.",
        "STAT 411": "Sequential Analysis. Topics: sequential tests, SPRT, optimal stopping.",
        "STAT 415": "Multivariate Statistical Analysis. Topics: PCA, factor analysis, MANOVA.",
        "COMP 102": "Introduction to Computers. Topics: hardware, software, basic programming concepts.",
        "COMP 104": "Computer Programming 1. Topics: Python/C basics, loops, functions, arrays.",
        "COMP 201": "Algorithm Design and Analysis. Topics: sorting, searching, complexity, dynamic programming.",
        "COMP 202": "Data Structures. Topics: linked lists, trees, graphs, hash tables, heaps.",
        "COMP 207": "Database Systems. Topics: SQL, ER diagrams, normalization, transactions.",
        "COMP 208": "Advanced Programming. Topics: OOP, design patterns, data structures in practice.",
        "COMP 212": "Advanced Computer Programming. Topics: advanced OOP, algorithms, software design.",
        "COMP 302": "Algorithm Specifications. Topics: formal methods, algorithm correctness, complexity proofs.",
        "COMP 304": "Compiler Design. Topics: lexical analysis, parsing, code generation, optimization.",
        "COMP 305": "Theory of Computation. Topics: automata, formal languages, Turing machines, complexity.",
        "COMP 307": "Operating Systems. Topics: processes, threads, memory management, file systems.",
        "COMP 308": "Cryptography. Topics: encryption, public key, hash functions, protocols.",
        "COMP 401": "Artificial Intelligence. Topics: search, knowledge representation, machine learning basics.",
        "COMP 403": "Parallel and Distributed Processing. Topics: parallel algorithms, concurrency, distributed systems, MPI/OpenMP.",
        "COMP 411": "Computational Engineering. Topics: numerical methods, scientific computing, simulations.",
    }

    msg_upper = user_message.upper()
    course_context = ""
    for code_key, topics in course_topics.items():
        if code_key in msg_upper or code_key.replace(" ", "") in msg_upper.replace(" ", ""):
            course_context = f"\nCOURSE TOPICS FOR {code_key}:\n{topics}\n"
            break

    sid   = student_data.get("ID", "N/A")
    cgpa  = student_data.get("CGPA", "N/A")
    hours = student_data.get("Earned_Hours", "N/A")
    level = student_data.get("Level", "N/A")
    admyr = student_data.get("Admission_Year", "N/A")
    lsgpa = student_data.get("Last_Semester_GPA", "N/A")

    prompt = (
        "You are an academic advisor for the Statistics and Computer Science program "
        "at Ain Shams University.\n\n"
        + lang_instruction + "\n\n"
        
        "## COMPARISON QUESTIONS\n"
       "If the student compares two courses:\n"
       "- explain why one course was prioritized\n"
       "- compare risk, prerequisites, graduation impact, and workload\n"
       "- recommend the safer or more strategic option\n"
       "- avoid generic answers\n\n"
       
       "## SEMESTER PLANNING\n"
       "When suggesting lighter loads:\n"
        "- explain WHICH types of courses should be avoided together\n"
        "- avoid recommending multiple heavy lab/project courses together\n"
        "- balance theory and practical courses\n\n"

        "## SCOPE\n"
        "Only answer questions about: course registration, academic rules, "
        "study strategies for program courses, GPA, prerequisites, "
        "and course recommendations.\n"
        "If the question is about ANYTHING else (food, sports, entertainment, coding help "
        "unrelated to their enrolled courses, personal life, general knowledge), "
        "respond with EXACTLY this and nothing else:\n"
        + refusal + "\n\n"

        "## PERSONALITY AND STYLE\n"
        "Only answer questions about: course registration, academic rules, study strategies.\n"
        "You are a confident, practical, direct advisor. Not a chatbot, not a report generator.\n"
        "- Do not repeat all provided data.\n"
        "- Only mention information relevant to the student's question.\n"
        "- Avoid sounding absolutely certain about future academic outcomes.\n"
        "- Present predictions as guidance, not guarantees.\n"
        "Talk to the student like a knowledgeable colleague.\n\n"

        "## STRICTLY BANNED PHRASES — never use these:\n"
        "- the system predicts / the prediction for you / our system / the model predicts\n"
        "- AI predicts / the data predicts / the prediction is / predicted probability\n"
        "- based on similar students (rephrase as: based on difficulty patterns in this course)\n"
        "- let's protect your GPA / good luck / I hope this helps / you've got this\n"
        "- super important / you totally have the ability\n"
        "- Never invent statistics, percentages, or university data.\n"
        "- Only use statistics explicitly provided in the prompt.\n"
        "- Do not claim historical pass/fail rates unless provided.\n\n"

        "## INSTEAD — use these framings:\n"
        "- 'You struggled with this course before, which means...\'\n"
        "- 'This course appears to be one of the more challenging courses based on your previous performance.\'\n"
        "- 'Given how this course went last time, you should expect...\'\n"
        "- 'Students who retake this course do better when they...\'\n\n"

        "## FORMATTING\n"
        "Use emoji headers only for relevant sections:\n"
        "  \u26a0\ufe0f Risk Analysis | \U0001f4d8 Why This Course | "
        "\u2705 Suggested Strategy | \U0001f4cb Policy | "
        "\U0001f4ca GPA Impact | \U0001f4da Study Tips\n"
        "Short paragraphs or tight bullets. Max 280 words. "
        "No numbered lists unless ranking matters.\n\n"

        "## ELECTIVE vs CORE LOGIC\n"
        "High fail risk + Core: must take eventually, reduce hours, get early help.\n"
        "High fail risk + Elective: advise skipping it, name a safer alternative.\n\n"
        

        "STUDENT PROFILE\n"
        f"ID: {sid} | CGPA: {cgpa} | Hours: {hours} | Level: {level} | "
        f"Last Sem GPA: {lsgpa} | Admitted: {admyr}\n\n"

        "ACADEMIC INSIGHTS\n"
        f"{insights_text}\n\n"

        "RULE ENGINE\n"
        f"{rule_summary}\n\n"

        "ML ANALYSIS\n"
        f"{ml_summary}\n\n"

        "COURSE HISTORY\n"
        f"{history_text}\n\n"

        "ACADEMIC RULES\n"
        f"{rag_text}\n"

        + course_context +

        (f"\nCURRENT PAGE CONTEXT\n{page_context}\n" if page_context else "")
        + "\nSTUDENT QUESTION\n"
        f"{user_message}\n"
    )

    return prompt
