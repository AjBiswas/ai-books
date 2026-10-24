"""Book 1, Chapter 47 lab (part 2): content credentials, the idea behind C2PA.

Instead of hiding a signal in the content, provenance ATTACHES a signed record: who made it, with
which tool, and a hash of the exact bytes. Anyone can check the record; any edit breaks the hash.
Real C2PA uses public-key certificates; this lab uses an HMAC so it runs with the standard library.
Run:  python provenance.py
"""
import hashlib
import hmac
import json

SIGNING_KEY = b"newsroom-camera-and-ai-tool-key"


def make_manifest(content: bytes, creator, tool, actions):
    claim = {"creator": creator, "tool": tool, "actions": actions, "sha256": hashlib.sha256(content).hexdigest()}
    sig = hmac.new(SIGNING_KEY, json.dumps(claim, sort_keys=True).encode(), hashlib.sha256).hexdigest()
    return {"claim": claim, "signature": sig}


def check(content: bytes, manifest):
    if manifest is None:
        return "no credentials: unknown origin (NOT proof it is fake)"
    claim = manifest["claim"]
    good_sig = hmac.compare_digest(manifest["signature"], hmac.new(SIGNING_KEY, json.dumps(claim, sort_keys=True).encode(), hashlib.sha256).hexdigest())
    if not good_sig:
        return "INVALID: the record itself was altered"
    if hashlib.sha256(content).hexdigest() != claim["sha256"]:
        return "INVALID: content changed after signing"
    return f"valid: made by {claim['creator']} with {claim['tool']}; actions: {', '.join(claim['actions'])}"


img = b"...pretend these are the bytes of a product photo..."
m = make_manifest(img, "Acme Marketing", "ImageGen v4", ["generated with AI", "cropped"])
print("1. original image + manifest      ->", check(img, m))
print("2. one byte changed               ->", check(img[:-1] + b"!", m))
forged = json.loads(json.dumps(m)); forged["claim"]["creator"] = "Reuters"
print("3. someone edits 'creator'        ->", check(img, forged))
print("4. screenshot (credentials lost)  ->", check(img, None))
