#!/bin/bash
cd /home/ubuntu/soko
export SOKO_SECRET=b5829e236bd60ed3ce4a9e381a148fb849cf427a158d4b945d81e5b59ca37702
export QUATTRO_KEY=qtt_2151e17a21ace1f16a5ef61d48ba892c4ff32cca
exec /home/ubuntu/soko-venv/bin/uvicorn app:app --host 0.0.0.0 --port 8090
