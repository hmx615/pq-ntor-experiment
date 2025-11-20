#!/bin/bash

# Clean up any running processes
killall -9 directory relay client 2>/dev/null
sleep 1

# Clean logs
rm -f *.log

# Start directory server (includes test HTTP server on port 8000)
./directory > directory.log 2>&1 &
DIR_PID=$!
sleep 2

# Start relays
./relay -r guard -p 6001 > guard.log 2>&1 &
GUARD_PID=$!

./relay -r middle -p 6002 > middle.log 2>&1 &
MIDDLE_PID=$!

./relay -r exit -p 6003 > exit.log 2>&1 &
EXIT_PID=$!

sleep 2

# Check if all servers started
ps -p $DIR_PID,$GUARD_PID,$MIDDLE_PID,$EXIT_PID > /dev/null
if [ $? -ne 0 ]; then
    echo "ERROR: Some servers failed to start"
    tail -20 *.log
    killall -9 directory relay 2>/dev/null
    exit 1
fi

echo "All servers started successfully"
echo "Directory: PID $DIR_PID"
echo "Guard:     PID $GUARD_PID"
echo "Middle:    PID $MIDDLE_PID"
echo "Exit:      PID $EXIT_PID"
echo ""

# Run client with HTTP request
echo "Running client..."
./client http://127.0.0.1:8000 2>&1 | tee client.log

# Show results
echo ""
echo "=== Test Complete ==="
echo ""
echo "Client output:"
cat client.log
echo ""

# Cleanup
killall -9 directory relay 2>/dev/null
