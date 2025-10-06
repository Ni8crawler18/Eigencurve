#!/usr/bin/env python3
import sys,socket
def main(h='127.0.0.1',p=9999):
    with socket.create_connection((h,int(p))) as s:
        f=s.makefile('r',encoding='utf-8',errors='replace')
        try:
            for line in f:
                if not line: break
                print(line.rstrip())
        except KeyboardInterrupt:
            pass
if __name__=='__main__':
    h=sys.argv[1] if len(sys.argv)>1 else '127.0.0.1'
    p=int(sys.argv[2]) if len(sys.argv)>2 else 9999
    print(f"Connecting to {h}:{p} — Ctrl+C to quit"); main(h,p)
