# Final working version of the key fixer
raw_key = """-----BEGIN PRIVATE KEY-----
MIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC33mVa2S31QiI0
d7iN0DCq/7zIRWnp/lGCoIutuyZNrtk2WTnendtTLskf5H+FfUnB0ajCC06FrjBf
boIfnaNYnlnTo8NKFBX+TVEM3eohrMFDQj0AYgasY3qXaMaX+LG1Z3Do8+8LuTPt
8kDl3QD86xQEhryf9CcGjIlxwISW4KG9vHhHS9WunH7uCZ4NG11n2wujRETdb5A8
nnkNf1CLlugvHDiUZiTEx1FQO/4hAk6SjyunusQK6GN4qUb2bS9GCLUt9jAYH9ZR
f2JdLoTuJRdWilZtNbA3+Fy0fOPcv/rGujG2XZHi0qVMggfqnX+zu7bv+sCb/cN4
wFdBSSE5AgMBAAECggEARjh8Uu7gm2svbwROCnL5M0VKDt5brc6/yHiR/76ayU4+
jIAVFs0Ix0L18uUsQonv0kLFBZ6V1X4J4Vht/68PhDetrKM9YRw8rgtPKe/SjBvT
D2HLtEq7q7iuSAbu2XlUPSiNOZp3r+2CRJyhZmg6CV2qHnRqs1fmU5z2nOfee1QW
kkg9a6hPz5vdn8OjqDVO1kCBInXoDF4WYP7Y5KcWRBy8n8V03D5Vo9WMAPCQHGaK
0FsT0uxThQ26Epb7j5OIYmLMwkEG3EUbJiftz0G+Xq/2WJQ6jlk0MLaeliTvZGwI
s4Cgtaz8wTsg33OIUKs+f5dIUUKEIHO9CZ12jNkgxQKBgQDq/ysYVIg/ezcHY9YL
jDbtO/y9h4uikPot3M4O9DkcHtsvSC1pIB24qFEFrc5dXOxVCJuEV77iPYEmyxxS
yzrpS+IFOUlv3bvCc1wMl2pT9UfJJSbaSEX8mUmR20wUBEfRMFPEtO2JKwv7z4mj
PKKQ5ungjuKWa8nl05Py2ommLwKBgQDITWU+UbmJs+qK94ReyAeFLJnvsVaFP3pG
on0wcqXb8GkHzpQuwLnagHCxLKfbMx2kx4QaiugbRTaPXoHLGNidKaDUio9ifpJv
/WeWdq1A31ojtb66j4lSnfgAluWUFtNygjTWbyMyJlqE2FWF2O7CdnnbHpz7wLzd
3dpE0E49FwKBgC56XWmofnIfyph5lIIgL1Togmpx/poelnyvqUmn4AvBxpQpcGHU
akx1beDzqVcp48xFsYyRVj2k8IBdt7JgY7x0t7VUyUOI1XP2IQSUhgEpCBOud2rA
1KbLIpPojbl/xzyGlGrZZgm1K9+YAp74hSanpSY23HXnx7zfBeoIcyUdAoGAEvxj
EFkmwQqwvKNhhKppLBJiNPoWPWMa7/8O5ry3Q/Wxvu+x1AyokTGDfQfCkWBy+t9+
ghWQkqUo2sYWf23Hen4rpHnNxYRB1SOr4fM10ORa4u+jOIPKfG5Ex6mF8VeIi14U
LA80wtgn1Fe9I4bAeuZH/qEUODi4rj8NJWCpSdkCgYBjNVJb7JE1kTL5t4E/RueA
gs25s/nh7dq87tbUullil2IFmyYVpp3u3hVBVXWfeAsheYnQVxWQxgIsoPvb2lHk
zZmLFx/4qjGYwrI/a3OvqXNwIBtHplc8ltd3WwRJmJ2mCSB8Ct1AB6hGyJt0VizQ
057lfnQwsE0Xgdu3epZhIQ==
-----END PRIVATE KEY-----"""

# Clean up any trailing/leading whitespace and empty lines
lines = [l.strip() for l in raw_key.split("\n") if l.strip()]
clean_key = "\\n".join(lines)

print("\n--- COPY EVERYTHING BETWEEN THESE LINES ---")
print(f'"{clean_key}"')
print("--- END ---")
