#!/bin/bash
echo "Killing all PQ-Tor processes..."
sudo killall -9 directory relay client 2>/dev/null || true
sleep 2
echo "Checking remaining processes..."
ps aux | grep -E "directory|relay|client" | grep -v grep | grep -v "kill_processes"
echo "Done!"
