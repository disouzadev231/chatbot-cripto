import base64

# Nome do arquivo de credenciais
input_file = "chatcriptomvp-sa.json"
output_file = "chave_base64.txt"

try:
    # Lê o arquivo JSON binariamente e converte para Base64
    with open(input_file, "rb") as f:
        base64_key = base64.b64encode(f.read()).decode("utf-8")

    # Salva a chave Base64 em um arquivo de texto
    with open(output_file, "w") as out:
        out.write(base64_key)

    print(f"✅ Base64 gerado com sucesso e salvo em '{output_file}'.")

except FileNotFoundError:
    print(f"❌ Arquivo '{input_file}' não encontrado.")
except Exception as e:
    print(f"❌ Erro ao gerar Base64: {e}")
