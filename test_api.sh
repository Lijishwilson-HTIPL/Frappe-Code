#!/bin/bash
export TERM=xterm
API_KEY="6993830736997b2"
API_SECRET="2fbd1328f867a2e"
AUTH=$(echo -n "${API_KEY}:${API_SECRET}" | base64)

echo "Testing process_payment..."
curl -s -X POST \
  http://127.0.0.1:8000/api/method/mft_integration.api.process_payment \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic ${AUTH}" \
  -d '{"stripe_session_id":"test_sess_abc123","name":"Test User","org":"Test Corp","email":"testuser@example.com","bill_number":"MFTBILL-99999"}' \
  | python3 -m json.tool
echo ""
