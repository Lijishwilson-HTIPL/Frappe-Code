#!/bin/bash
export TERM=xterm
cd /home/paul/frappe-bench
source env/bin/activate
echo "mysite.local" > sites/currentsite.txt

# Kill existing screen sessions for erpnext
screen -S erpnext -X quit 2>/dev/null || true
sleep 1

# Kill anything on port 8000
fuser -k 8000/tcp 2>/dev/null || true
sleep 1

# Start bench serve inside a detached screen session
screen -dmS erpnext bash -c "cd /home/paul/frappe-bench && source env/bin/activate && echo mysite.local > sites/currentsite.txt && bench serve --port 8000 2>&1 | tee /tmp/erpnext_web.log"

sleep 3
if screen -list | grep -q erpnext; then
  echo "ERPNext screen session running ok"
else
  echo "ERROR: screen session failed to start"
fi
