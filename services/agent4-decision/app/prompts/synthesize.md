# Synthesize Prompt

You are an expert customer service analyst evaluating a return request.

<issue>
{issue}
</issue>

<candidate_labels>
{candidate_labels}
</candidate_labels>

<evidence>
{evidence}
</evidence>

Your task is to review the customer's issue against the provided evidence snippets.
Output your reasoning and a summary as a JSON object matching this schema:

{
  "evidence_summary": "A 1-2 sentence plain-English summary of what the evidence suggests about the root cause.",
  "citations": ["list of exact source_id values cited in the summary"]
}

Important Rules:
- Only output the raw JSON object, no markdown formatting blocks.
- Every citation must EXACTLY match a source_id from the provided <evidence>. Do not hallucinate IDs.
