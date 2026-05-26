redis_cache: redis-server config/redis_cache.conf

redis_queue: redis-server config/redis_queue.conf

web: /home/hilton/.local/bin/bench serve --port 8000

socketio: /home/hilton/.nvm/versions/node/v18.20.8/bin/node apps/frappe/socketio.js

watch: /home/hilton/.local/bin/bench watch

schedule: /home/hilton/.local/bin/bench schedule

worker: /home/hilton/.local/bin/bench worker 1>> logs/worker.log 2>> logs/worker.error.log
