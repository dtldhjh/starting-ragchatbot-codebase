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
payload = {
    'model': os.environ.get('MODEL', 'meta/llama-3.1-8b-instruct'),
    'messages': [
        {'role': 'system', 'content': 'You are a senior code reviewer. Review the git diff for bugs, security issues, and improvements. Be concise.'},
        {'role': 'user', 'content': 'Review this diff:\n\n' + diff}
    ],
    'temperature': 0.3,
    'max_tokens': 2000
}
print(json.dumps(payload))
PYEOF

PAYLOAD=$(python3 /tmp/review.py)
RESPONSE=$(curl -s -X POST "$BASE_URL/chat/completions" -H "Content-Type: application/json" -H "Authorization: Bearer $API_KEY" -d "$PAYLOAD")

echo "Response preview: ${RESPONSE:0:500}"

REVIEW=$(echo "$RESPONSE" | python3 -c "import sys,json; data=json.load(sys.stdin); print(data.get('choices',[{}])[0].get('message',{}).get('content','Error: no response'))")

echo "$REVIEW" > /tmp/review.txt
echo "review=true" >> $GITHUB_OUTPUT
