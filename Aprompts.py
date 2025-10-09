
Quality_sys_prompt = """
You are a professional text quality evaluation expert. I will provide you with a research question and a report, please evaluate the quality of the report.
"""

Quality_user_prompt = """

Please objectively evaluate the quality of the following report based on these four criteria, and provide scores out of 4 for each:

(1) Comprehensiveness and Depth: The report should cover all key aspects of the topic, with detailed and in-depth analysis.
(2) Structural Clarity and Logic: The report should be well-organized, with clear structure and logical flow.
(3) Fluency and Consistency of Expression: The language should be fluent, accurate, and professional, with a consistent style.
(4) Material Integration and Originality: The report should demonstrate independent thinking, effective integration of materials, and avoid simple patchwork or direct copying.

Overall Report Scoring (0–4 Points)
1. Comprehensive and In-depth Content
| Score | Description |
|-------|-------------|
| 4 | The content is comprehensive, all necessary elements are present, information is detailed, analysis is in-depth, viewpoints are profound, and there are no significant omissions. |
| 3 | The content is relatively complete, most key elements are included, the analysis has some depth, and minor details are lacking but do not affect overall understanding. |
| 2 | Some content is missing, important information is not covered, the analysis is superficial, and this affects a comprehensive understanding of the topic. |
| 1 | The content is seriously incomplete, key elements are missing, the analysis is shallow, and the information is insufficient to support the topic. |
| 0 | The content is extremely lacking, there is almost no valid information, no depth at all, and it cannot form an effective report. |
2. Clear and Logical Structure
| Score | Description |
|-------|-------------|
| 4 | The structure is clear and logical, each part is well-organized, transitions are smooth, and the report is easy to understand. |
| 3 | The structure is generally reasonable and logical, but some paragraphs are slightly disorganized or transitions are awkward. |
| 2 | The structure is rather loose, lacking natural segmentation and clear transitions, and the logical relationships are not clear enough. |
| 1 | The structure is chaotic, with large logical leaps, making it difficult for readers to follow the train of thought. |
| 0 | There is no discernible structure, the content is arranged chaotically, and the logic is completely unclear. |
3. Fluent and Consistent Expression
| Score | Description |
|-------|-------------|
| 4 | The language is fluent and accurate, the style is consistent and professional, with no redundancy or improper word usage. |
| 3 | The expression is generally clear, the writing style is mostly consistent, with occasional repetition or lack of conciseness. |
| 2 | There is considerable redundancy or improper word usage, sentences are not smooth, and the style is somewhat inconsistent. |
| 1 | The language is confusing, with serious repetition, and the writing style is chaotic. |
| 0 | The expression is extremely poor, comprehension is affected, there are frequent grammatical errors, and it is difficult to read. |
4. Material Integration and Originality
| Score | Description |
|-------|-------------|
| 4 | The content is highly original, with almost no material patchwork; analysis is based on a deep understanding and reprocessing of materials, and independent insights are prominent. |
| 3 | Independent analysis is predominant, material patchwork is rare, and cited materials are effectively integrated and processed. |
| 2 | Material patchwork is obvious, analysis mostly relies on direct quotations, and there is a lack of in-depth processing and independent insights. |
| 1 | The content mainly consists of simple listing of materials, with little analysis; most content is directly excerpted, and personal thinking is almost absent. |
| 0 | The entire report is a patchwork or direct copy of materials, with no analysis at all; the content is mechanically pieced together and completely lacks originality. |
5. Overall, do you like this report? Why? 
| Score | Description |
|------|-------------|
| 4 | Like it very much. |
| 3 | Like it. |
| 2 | It's average. |
| 1 | Don't like it much. |
| 0 | Don't like it at all. |

Notes:
- A satisfactory performance deserves around 2 points, with higher scores for excellence and lower scores for deficiencies.
- You should not easily assign scores higher than 3 or lower than 1 unless you provide substantial reasoning.

- Please provide the final scores in the following JSON format:
{{
    "Reason": <reasoning for the scores>,
    "Comprehensiveness_Score": <score>,
    "Coherence_Score": <score>,
    "Clarity_Score": <score>,
    "Insightfulness_Score": <score>, 
    "Overall_Score": <score>
}}


Research Question:
{question}

Research Paragraphs:
{paragraph}


"""

FACT_CHECK_SYS_PROMPT = """
# Factual Evaluation
Given a piece of web content and a sentence from a report, please determine whether the information expressed in the sentence can be directly found in or reasonably inferred from the provided web content.

# Important Notes
- Please do not rely on your external knowledge; make judgments solely based on the provided web content
- Pay attention to key terms in the statement (such as time, location, people, quantities, etc.), ensuring these details have corresponding or derivable information in the web content
- If the statement contains multiple information points, please evaluate each one to determine if they can all be supported by the web content

## Scoring Criteria
- **Fully Supported**:
  - The web content explicitly mentions information that is identical to or highly relevant to the statement, allowing direct verification of the statement as true
  - Or, through reasonable inference from multiple information points in the web content, a conclusion consistent with the statement can be reached
- **Partially Supported**:
  - The web content contains some relevant information, but it is insufficient to fully confirm or deny the statement
  - Or the information is ambiguous, making it impossible to make a clear judgment
- **Not Supported**:
  - The web content does not mention any information related to the statement
  - Or the web content clearly contradicts the statement, allowing the statement to be determined as false


Please return the analysis result in JSON format:
{
    "is_factual": -1/0/1, # -1: not supported, 0: partially supported, 1: fully supported
    "sentence_support": "Specific sentences from the web content that can support this fact"
}
"""

FACT_CHECK_USER_PROMPT = """
Here is the content of the website:
{url_markdown}

Here is the sentence:
{input}
"""

REPEATABILITY_SYSTEM_PROMPT = """
Given two paragraphs, please assess the degree of content repetition between them. 
You should analyze from multiple perspectives and assign a reasonable score based on the scoring criteria.

# What is "Repetition":

Repetition of viewpoints or content: The two paragraphs express the same or highly similar viewpoints, themes, or conclusions, regardless of whether they are rephrased.
Repetition of examples, data, or references: The same cases, data, facts, or sources are used, or the same content is rephrased or paraphrased.
Implicit repetition: Although the wording is different, the core information, arguments, or conclusions are essentially the same.

# What is NOT "Repetition":
Differences in expression: Only the language, sentence structure, or style is different, but the information content and core viewpoints are not the same.
Related topics but different content: The topics are similar, but the information, arguments, or conclusions conveyed are different.
Supplementation and extension: One paragraph supplements, expands upon, or introduces new viewpoints to the other, rather than simply repeating it.

# Notes
Focus on content: Concentrate on repetition at the information level, not just superficial language or stylistic differences.
Consider both explicit and implicit repetition:
Explicit repetition: Direct copying or nearly identical text.
Implicit repetition: Expressing the same information through paraphrasing, summarizing, etc.
Consider contextual impact: Assess whether the repetition affects readability and information density.
Avoid subjective bias: Do not rely on personal knowledge or judgments about the correctness of the content; score only based on whether repetition exists between the paragraphs.

# Scoring Criteria
Use a 0–4 point scale to evaluate the degree of repetition between paragraphs:
4 points (Almost no repetition): The paragraphs are completely independent, with no repeated viewpoints, examples, or expressions.
3 points (Slight repetition): There are 1–2 minor instances of content repetition, but they do not affect the overall reading experience.
2 points (Some repetition): There are multiple instances of content repetition, which somewhat affect the reading experience.
1 point (Severe repetition): There is a large amount of content repetition, which seriously affects the quality of the writing.
0 points (Excessive repetition): Almost all content is repeated, and the value of the writing is lost.


# Important Notes:
- Please do not rely on your external knowledge; make judgments solely based on the provided content
- Note that using the same example to explain different concepts is not considered repetition

# Some tips may help you:
- Check if the paragraphs contain the same quotations
- Check if the paragraphs follow the same logical flow

# Some Examples
Paragraph 1:
Teamwork is essential for achieving organizational goals. When team members collaborate, they can share ideas, solve problems together, and increase productivity. Effective teamwork also improves communication and builds trust among members, which leads to a more harmonious work environment. Without teamwork, organizations may struggle to reach their objectives efficiently.
Paragraph 2:
Teamwork is essential for achieving organizational goals. When team members collaborate, they can share ideas, solve problems together, and increase productivity. Effective teamwork also improves communication and builds trust among members, which leads to a more harmonious work environment. Without teamwork, organizations may struggle to reach their objectives efficiently.
Output:
{
    "score": 0,
    "explanation": "The two paragraphs are completely identical in content, wording, and structure. Every viewpoint, example, and conclusion is repeated without any difference.",
    "repetitions_found": [
        "Teamwork is essential for achieving organizational goals.",
        "When team members collaborate, they can share ideas, solve problems together, and increase productivity.",
        "Effective teamwork also improves communication and builds trust among members, which leads to a more harmonious work environment.",
        "Without teamwork, organizations may struggle to reach their objectives efficiently."
    ],
    "confidence": "100%"
}

Paragraph 1:
Teamwork is essential for achieving organizational goals. When team members work together, they can share ideas, solve problems collectively, and increase overall productivity. Furthermore, effective teamwork enhances communication and builds trust among colleagues, creating a positive and supportive work environment. Organizations that lack teamwork often face challenges in reaching their targets efficiently.
Paragraph 2:
Achieving organizational goals greatly depends on teamwork. By collaborating, team members are able to exchange ideas, address challenges as a group, and improve productivity. In addition, good teamwork fosters better communication and trust, which are crucial for a harmonious workplace. Without strong teamwork, organizations may find it difficult to accomplish their objectives.
Output:
{
    "score": 1,
    "explanation": "Most of the content is repeated between the two paragraphs. The main viewpoints, examples, and conclusions are the same, with only minor differences in wording.",
    "repetitions_found": [
        "Teamwork is essential for achieving organizational goals / Achieving organizational goals greatly depends on teamwork.",
        "Team members share ideas, solve problems together, and increase productivity.",
        "Effective teamwork improves communication and builds trust among colleagues, creating a positive work environment.",
        "Organizations without teamwork struggle to reach their objectives."
    ],
    "confidence": "95%"
}


Paragraph 1:
Teamwork plays a vital role in helping organizations reach their goals. When individuals collaborate, they can share their unique perspectives and solve problems more effectively. Teamwork also helps distribute the workload evenly, preventing burnout and ensuring that tasks are completed on time. Moreover, working in teams can inspire creativity and innovation, as members build on each other’s ideas.
Paragraph 2:
The importance of teamwork in organizations cannot be overstated. By working together, employees can share ideas and solve problems as a group, which often leads to better solutions. Additionally, teamwork can improve job satisfaction and foster a sense of belonging among employees. When people feel they are part of a team, they are more likely to be motivated and committed to their work.
Output:
{
    "score": 2,
    "explanation": "There are multiple instances of content repetition, such as sharing ideas and solving problems together, but each paragraph also contains unique points (e.g., preventing burnout, inspiring creativity, job satisfaction, sense of belonging).",
    "repetitions_found": [
        "Teamwork helps organizations/employees share ideas and solve problems together."
    ],
    "confidence": "90%"
}


Paragraph 1:
Participating in a marathon is an excellent way to improve one’s physical endurance. For instance, both the Boston Marathon and the New York City Marathon require runners to train for months, gradually increasing their running distance and stamina. Compared to local 5K races, these world-famous marathons demand a much higher level of physical preparation, pushing athletes to reach new heights in cardiovascular fitness and muscle strength. This highlights how marathon events serve as a benchmark for testing and enhancing physical capabilities.
Paragraph 2:
Marathon running is also a powerful tool for building mental resilience. Take the Boston Marathon as an example: while the event is renowned for its challenging course, what truly sets it apart is the psychological battle runners face, especially when tackling the infamous Heartbreak Hill. Unlike local 5K races, where the mental challenge is relatively minor, marathon participants must overcome self-doubt and fatigue over several hours. This demonstrates that marathons not only test the body but also cultivate perseverance and mental toughness.
Output:
{
    "score": 3,
    "explanation": "There is only slight repetition. Both paragraphs use the example of the Boston Marathon, but Paragraph 1 focuses on physical endurance and training, while Paragraph 2 emphasizes mental resilience and psychological challenges.",
    "repetitions_found": [
        "Both paragraphs mention the Boston Marathon as a key example."
    ],
    "confidence": "85%"
}


Paragraph 1:
Teamwork fosters creativity by bringing together people with diverse backgrounds and skill sets. When individuals with different perspectives collaborate, they can generate innovative solutions that might not have been possible working alone. This diversity of thought is a key driver of progress and adaptability in today’s fast-changing business environment.

Paragraph 2:
Teamwork also plays a crucial role in conflict resolution within organizations. When disagreements arise, a strong team can address issues openly and constructively, ensuring that all voices are heard and a consensus is reached. This ability to manage and resolve conflicts effectively contributes to a healthier and more productive workplace.

Output:
{
    "score": 4,
    "explanation": "The two paragraphs are completely independent. One discusses creativity from diverse backgrounds, the other focuses on conflict resolution. There are no repeated viewpoints, examples, or expressions.",
    "repetitions_found": [],
    "confidence": "100%"
}


# Output Format
Must output a JSON object with the following fields:

{
    "score": "0-4 score based on above criteria",
    "explanation": "Explanation of score with specific examples of repetition",
    "repetitions_found": [the repeated content1,the repeated content2,the repeated content3,...],
    "confidence": "Confidence in assessment (0%-100%)"
}

# Output Example:
{
    "score": 3,
    "explanation": "Score of 3 given due to low overall repetition, with only one unnecessary repetition in describing [concept].",
    "repetitions_found": [the repeated content1,the repeated content2,the repeated content3,...],
    "confidence": 90
}


"""
REPEATABILITY_USER_PROMPT = """Please evaluate the degree of repetition between paragraphs in the following <paragraphs>.

Paragraph 1:
{para1}
--paragraph1 end--




Paragraph 2:
{para2}
--paragraph2 end--
output:

"""
