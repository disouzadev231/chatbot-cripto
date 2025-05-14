import base64

with open("chatcriptomvp-sa.json", "rb") as f:
    encoded = base64.b64encode(f.read()).decode("utf-8")
    with open("chave_base64.txt", "w") as out:
        out.write(encoded)

print("✅ Chave convertida com sucesso!")
