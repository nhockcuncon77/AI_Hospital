"""
Check server health: call /, /health, /twiml with Flask test client (no port needed).
Run: python check_health.py
"""
import sys

def main():
    from server import app
    # Test client does not need a port
    client = app.test_client()
    ok = True
    for path, name in [("/", "root"), ("/health", "health"), ("/twiml?scenario_id=schedule_new", "twiml")]:
        try:
            r = client.get(path)
            body = (r.data or b"").decode("utf-8", errors="replace")[:120]
            print(f"  {name}: {r.status_code}  {body[:70]}{'...' if len(body) > 70 else ''}")
            if r.status_code != 200:
                ok = False
        except Exception as e:
            print(f"  {name}: FAILED - {e}")
            ok = False
    print("")
    if ok:
        print("Server health OK. Flask routes respond correctly.")
        print("To serve over the network: run 'python server.py' (listens on port 5050 by default).")
    else:
        print("Some checks failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
