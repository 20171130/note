   
When debugging:

Always identify the root cause before attempting any fix.

If the cause is obvious, clearly explain it to the user.

If the cause is not obvious, propose plausible hypotheses and discuss them with the user.

Only after the user approves a hypothesis, add targeted debug logging or instrumentation to test it.

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔴 USER PRINCIPLES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

0. CLARIFY FIRST  
   If anything is confusing, ambiguous, or unexpected, pause and ask the user for further instructions.

1. MINIMIZE CODE  
   Write only what is explicitly requested. Do not add anything extra.

2. NO DOCUMENTATION  
   Do not add documentation unless explicitly requested.  
   → Preserve existing user-written docs/comments (fix grammar or typos only).  
   → No docstrings, READMEs, or additional comments.

3. LET IT CRASH  
   Do not add error handling, unless it is expected like network unstability.
   → No try/except blocks, guards, or fallback branches.  
   → Stack traces are valuable for debugging; error handling hides bugs.  
   → Do not add checks like `if x is not None` when `x` is expected to exist.

4. NO UNEXPECTED DEFAULT VALUES  
   → Do not use safe accessors like `dict.get(key, default)` or `getattr(obj, attr, default)`.  
   → Default values are allowed **only** in function signatures and `argparse`.  
   → If a required key or attribute is missing, let the program crash.