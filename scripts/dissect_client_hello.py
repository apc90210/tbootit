import subprocess
import struct

SSH_KEY = r"C:\Users\Apc\.ssh\id_ed25519"
VDS_HOST = "root@144.31.50.134"

remote_script = """
import subprocess
import struct

cmd = "tcpdump -nn -r /tmp/stage10c_r2_owner_nonvpn.pcap 'host 217.151.227.96 and src port 3479' -x"
out = subprocess.run(cmd, shell=True, capture_output=True, text=True).stdout

hex_lines = []
capturing = False
for line in out.splitlines():
    if "08:11:29.739160" in line:
        capturing = True
        continue
    if capturing:
        if line.startswith("\t"):
            parts = line.strip().split()
            for p in parts[1:]:
                hex_lines.append(p)
        else:
            break

raw_hex = "".join(hex_lines)
data = bytes.fromhex(raw_hex)
print(f"Total raw bytes: {len(data)}")

ip_hdr_len = (data[0] & 0x0f) * 4
tcp_offset = ip_hdr_len
tcp_hdr_len = ((data[tcp_offset + 12] >> 4) & 0x0f) * 4
payload = data[tcp_offset + tcp_hdr_len:]
print(f"Payload length: {len(payload)}")

if len(payload) >= 5:
    content_type, ver, rec_len = struct.unpack("!BHH", payload[:5])
    print(f"TLS Content Type: {content_type} (22=Handshake)")
    print(f"TLS Version: 0x{ver:04x}")
    print(f"TLS Record Length: {rec_len}")
    
    if content_type == 22 and len(payload) >= 9:
        hs_type = payload[5]
        hs_len = int.from_bytes(payload[6:9], 'big')
        print(f"Handshake Type: {hs_type} (1=ClientHello)")
        print(f"Handshake Length: {hs_len}")
        
        pos = 9
        cl_ver = struct.unpack("!H", payload[pos:pos+2])[0]
        pos += 2 + 32 # skip version & random
        sess_id_len = payload[pos]
        pos += 1 + sess_id_len
        cs_len = struct.unpack("!H", payload[pos:pos+2])[0]
        pos += 2 + cs_len
        comp_len = payload[pos]
        pos += 1 + comp_len
        
        if pos + 2 <= len(payload):
            ext_len = struct.unpack("!H", payload[pos:pos+2])[0]
            pos += 2
            print(f"Extensions Length in record: {ext_len}")
            ext_data = payload[pos:]
            
            ext_pos = 0
            while ext_pos + 4 <= len(ext_data):
                etype, elen = struct.unpack("!HH", ext_data[ext_pos:ext_pos+4])
                ext_pos += 4
                edata = ext_data[ext_pos:min(ext_pos+elen, len(ext_data))]
                ext_pos += elen
                print(f"  Extension 0x{etype:04x} ({etype}): len={elen}")
                if etype == 0: # server_name
                    print(f"    server_name: {edata}")
                elif etype == 16: # ALPN
                    print(f"    ALPN: {edata}")
                elif etype == 0x0033: # key_share
                    print(f"    key_share length: {elen}")
                elif etype == 0xfe0d: # Encrypted Client Hello (ECH) draft
                    print(f"    ECH (Encrypted Client Hello) detected! len={elen}")
"""

proc = subprocess.run(
    ["ssh", "-i", SSH_KEY, "-o", "BatchMode=yes", VDS_HOST, "python3"],
    input=remote_script,
    capture_output=True,
    text=True
)

print(proc.stdout)
if proc.stderr:
    print("STDERR:", proc.stderr)
