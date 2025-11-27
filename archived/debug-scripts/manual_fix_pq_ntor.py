#!/usr/bin/env python3
"""
Manually read, fix, and write pq_ntor.c
"""

import paramiko

HOST = "192.168.5.110"
PORT = 22
USER = "user"
PASSWORD = "user"

def main():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname=HOST, port=PORT, username=USER, password=PASSWORD,
               allow_agent=False, look_for_keys=False)

    fix_cmd = """
cd /home/user/pq-ntor-experiment/c/src

# Restore from backup
cp pq_ntor.c.backup pq_ntor.c

# Create Python script to do the fix
cat > fix_pq_ntor.py << 'PY_EOF'
#!/usr/bin/env python3

with open('pq_ntor.c', 'r') as f:
    lines = f.readlines()

output = []
i = 0
while i < len(lines):
    line = lines[i]

    # Find the identity check section
    if '// 验证 relay_identity' in line:
        # Add ifndef before this section
        output.append('#ifndef USE_LOCAL_MODE\n')
        output.append(line)  # // 验证 relay_identity
        i += 1
        output.append(lines[i])  # if (memcmp...
        i += 1
        output.append(lines[i])  # fprintf...
        i += 1
        output.append(lines[i])  # return PQ_NTOR_ERROR
        i += 1
        output.append(lines[i])  # }
        output.append('#else\n')
        output.append('    /* Skip identity verification in local mode */\n')
        output.append('#endif\n')
    else:
        output.append(line)

    i += 1

with open('pq_ntor.c', 'w') as f:
    f.writelines(output)

print("✅ 修复完成")
PY_EOF

python3 fix_pq_ntor.py

# Show the result
echo ""
echo "=== 修复后的代码 ==="
grep -B 2 -A 8 "验证 relay_identity" pq_ntor.c

# Recompile
cd /home/user/pq-ntor-experiment/c
make clean > /dev/null 2>&1
make relay client

echo ""
ls -lh relay client
"""

    stdin, stdout, stderr = ssh.exec_command(fix_cmd, timeout=180)

    print(stdout.read().decode('utf-8'))
    err = stderr.read().decode('utf-8')
    if err:
        print("编译输出:", err)

    ssh.close()

if __name__ == "__main__":
    main()
