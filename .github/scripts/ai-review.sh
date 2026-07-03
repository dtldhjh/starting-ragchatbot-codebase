#!/bin/bash
API_KEY="${AI_API_KEY}"
BASE_URL="${AI_BASE_URL:-https://api.openai.com/v1}"
MODEL="${AI_MODEL:-meta/llama-3.1-8b-instruct}"
DIFF=$(echo "$DIFF_BASE64" | base64 -d)

if [ -z "$API_KEY" ] || [ -z "$DIFF" ]; then
  echo "Skipping: no API key or empty diff"
  exit 0
fi

echo "$DIFF" > /tmp/diff.txt

cat > /tmp/review.py << 'PYEOF'
import json, os
with open('/tmp/diff.txt') as f:
    diff = f.read()

SYSTEM_PROMPT = """You are an expert code reviewer reviewing a GitHub PR diff.

IMPORTANT CONTEXT:
- This is a GitHub Actions workflow
- Secrets are accessed via ${{ secrets.SECRET_NAME }} syntax - these are SECURE and not plain text
- Environment variables like ${{ env.VAR }} are also secure
- Focus on REAL issues only, not hypothetical ones

REVIEW GUIDELINES:
1. **Bugs**: Logic errors, null pointer issues, off-by-one errors
2. **Security**: Actual vulnerabilities (SQL injection, XSS, hardcoded credentials)
3. **Performance**: Obvious bottlenecks, N+1 queries, missing indexes
4. **Code Quality**: Unclear naming, missing error handling, duplicated code

DO NOT flag:
- GitHub secrets usage (they are secure by design)
- Style preferences (unless extreme)
- Theoretical issues without evidence

Be concise and actionable. Only mention real problems."""

payload = {
    'model': os.environ.get('MODEL', 'meta/llama-3.1-8b-instruct'),
    'messages': [
        {'role': 'system', 'content': SYSTEM_PROMPT},
        {'role': 'user', 'content': 'Review this PR diff:\n\n' + diff}
    ],
    'temperature': 0.2,
    'max_tokens': 3000
}
print(json.dumps(payload))
PYEOF

PAYLOAD=$(python3 /tmp/review.py)
RESPONSE=$(curl -s -X POST "$BASE_URL/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer $API_KEY" -d "$PAYLOAD")

echo "Response preview: ${RESPONSE:0:500}"

REVIEW=$(echo "$RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('choices',[{}])[0].get('message',{}).get('content','Error: no response'))")

echo "$REVIEW" > /tmp/review.txt
echo "review=true" >> $GITHUB_OUTPUT
