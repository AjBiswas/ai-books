"""Chapter 12 lab: redact Indian PII before any model sees it, restore it after."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from harness.policy import redact, restore, verhoeff_check_digit

base = "49871234560"                       # synthetic, not a real person
aadhaar = base + verhoeff_check_digit(base)
fake = base + str((int(aadhaar[-1]) + 3) % 10)
msg = (f"Hi, I'm Priya (priya.k@example.in, +91 98450 12345 -> 9845012345). "
       f"Aadhaar {aadhaar[:4]} {aadhaar[4:8]} {aadhaar[8:]}, PAN ABCDE1234F, card 4111 1111 1111 1111. "
       f"Order ref {fake} please.")
vault = {}
safe, found = redact(msg, vault)
print("original:", msg)
print("to model:", safe)
print("found:   ", sorted(set(found)))
print("restored == original:", restore(safe, vault) == msg)
print(f"(the 12-digit order ref {fake} fails the Aadhaar checksum, so it is left alone)")
