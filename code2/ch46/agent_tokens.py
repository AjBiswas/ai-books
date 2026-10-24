"""Book 1, Chapter 46 lab: identities and scoped, short-lived tokens for AI agents.

An agent is a non-human identity. It should never borrow a human's password or a forever API key.
This lab issues signed tokens (like a tiny JWT) that say WHO the agent is, ON BEHALF OF whom it acts,
WHAT it may do (scopes) and UNTIL WHEN. The tool server checks every call and writes an audit log.
Run:  python agent_tokens.py      (standard library only)
"""
import base64
import hashlib
import hmac
import json

SECRET = b"identity-provider-signing-key"      # held by the identity provider, never by the agent


def b64(d):
    return base64.urlsafe_b64encode(json.dumps(d, separators=(",", ":")).encode()).decode().rstrip("=")


def issue(agent, on_behalf_of, scopes, ttl_s, now):
    claims = {"sub": agent, "act_for": on_behalf_of, "scope": scopes, "exp": now + ttl_s}
    body = b64(claims)
    sig = hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()[:32]
    return f"{body}.{sig}"


def verify(token, now):
    body, sig = token.rsplit(".", 1)
    if not hmac.compare_digest(sig, hmac.new(SECRET, body.encode(), hashlib.sha256).hexdigest()[:32]):
        raise PermissionError("bad signature (token was edited)")
    claims = json.loads(base64.urlsafe_b64decode(body + "=" * (-len(body) % 4)))
    if now > claims["exp"]:
        raise PermissionError("token expired")
    return claims


AUDIT = []


def tool_server(token, action, now):
    """Every tool call carries a token; the server decides, and remembers."""
    try:
        c = verify(token, now)
    except PermissionError as e:                   # identity unproven: log it as unknown
        c, result = {"sub": "?", "act_for": "?"}, f"DENIED: {e}"
    else:
        result = "ok" if action in c["scope"] else f"DENIED: scope '{action}' not granted"
    AUDIT.append((now, c["sub"], c["act_for"], action, result))
    return result


now = 1_000_000
tok = issue("agent:travel-bot", "user:asha", ["calendar.read", "flights.search"], ttl_s=900, now=now)
print("token issued for 15 minutes:", tok[:60] + "...")
print("decoded claims:", verify(tok, now))

print("\ncalls:")
for t, action, label in [
    (tok, "calendar.read", "read Asha's calendar"),
    (tok, "flights.search", "search flights"),
    (tok, "flights.book", "book a flight (not in scope)"),
]:
    print(f"   {label:32} -> {tool_server(t, action, now + 60)}")

# a prompt-injected agent tries to give itself more power by editing its token
body, sig = tok.rsplit(".", 1)
claims = verify(tok, now)
claims["scope"].append("payments.send")
forged = b64(claims) + "." + sig
print(f"   {'forged token adds payments.send':32} -> {tool_server(forged, 'payments.send', now + 120)}")

# the same token later
print(f"   {'search flights, 20 minutes later':32} -> {tool_server(tok, 'flights.search', now + 1200)}")

# a human approves booking: a NEW narrow token, for one action, for 2 minutes
tok2 = issue("agent:travel-bot", "user:asha", ["flights.book"], ttl_s=120, now=now + 1300)
print(f"   {'book after Asha approves':32} -> {tool_server(tok2, 'flights.book', now + 1310)}")

print("\naudit log (who, for whom, what, result):")
for t, sub, who, action, res in AUDIT:
    print(f"   t+{t - now:4d}s  {sub:17} for {who:10} {action:15} {res}")
