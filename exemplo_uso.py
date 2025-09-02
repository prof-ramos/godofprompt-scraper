#!/usr/bin/env python3
"""
Exemplo de uso do GodOfPrompt Scraper
Este arquivo demonstra como usar o scraper de forma programática
"""

import json
from extract_links import extract_category_links, load_categories

def exemplo_extracao_basica():
    """Exemplo básico de extração de uma categoria"""
    print("🚀 Exemplo: Extração Básica")
    print("=" * 50)

    # Carregar categorias
    categories = load_categories()
    print(f"Categorias disponíveis: {[cat['nome'] for cat in categories]}")

    # Escolher primeira categoria
    categoria = categories[0]
    print(f"\nSelecionada: {categoria['nome']}")
    print(f"URL: {categoria['link']}")
    print(f"Prompts esperados: {categoria['quantidadeDePrompts']}")

    # Extrair links (removido para demonstração)
    # prompts = extract_category_links(categoria)

    print("\nPara executar a extração real:")
    print(f"python3 extract_links.py --test \"{categoria['nome']}\"")

def exemplo_analise_resultados():
    """Exemplo de análise dos resultados extraídos"""
    print("\n📊 Exemplo: Análise de Resultados")
    print("=" * 50)

    # Simulação de dados extraídos
    exemplo_dados = {
        "Vendas": {
            "quantidade_esperada": 252,
            "quantidade_extraida": 245,
            "prompts": [
                {
                    "url": "https://www.godofprompt.ai/prompt?prompt=sales-script",
                    "name": "Sales Script Generator",
                    "id": "sales-script",
                    "category": "sales"
                },
                {
                    "url": "https://www.godofprompt.ai/prompt?prompt=cold-email",
                    "name": "Cold Email Template",
                    "id": "cold-email",
                    "category": "sales"
                }
            ]
        }
    }

    # Análise básica
    categoria = "Vendas"
    dados = exemplo_dados[categoria]

    print(f"Categoria: {categoria}")
    print(f"Esperado: {dados['quantidade_esperada']}")
    print(f"Extraído: {dados['quantidade_extraida']}")
    print(f"Taxa de sucesso: {(dados['quantidade_extraida'] / dados['quantidade_esperada']) * 100:.1f}%")
    print(f"Primeiros prompts encontrados:")
    for i, prompt in enumerate(dados['prompts'][:3], 1):
        print(f"  {i}. {prompt['name']}")
        print(f"     URL: {prompt['url']}")

def exemplo_configuracao_personalizada():
    """Exemplo de configuração personalizada"""
    print("\n⚙️  Exemplo: Configuração Personalizada")
    print("=" * 50)

    # Configurações possíveis
    config = {
        "max_workers": 3,  # Workers para processamento concorrente
        "page_timeout": 30,  # Timeout em segundos
        "max_pages_per_category": 50,  # Máximo de páginas por categoria
        "request_delay": 2,  # Delay entre requests
        "output_format": "json",  # Formato de saída
        "enable_logging": True,  # Habilitar logging detalhado
        "enable_cache": True,  # Habilitar cache de requests
    }

    print("Configurações recomendadas:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    print("\nPara modificar essas configurações, edite o arquivo extract_links.py")

def exemplo_tratamento_erros():
    """Exemplo de tratamento de erros"""
    print("\n🛡️  Exemplo: Tratamento de Erros")
    print("=" * 50)

    print("Cenários comuns de erro e soluções:")
    print()
    print("1. Timeout na página:")
    print("   - Aumentar PAGE_LOAD_TIMEOUT no código")
    print("   - Verificar conexão com internet")
    print()
    print("2. Elemento não encontrado:")
    print("   - Verificar se o seletor Wized mudou")
    print("   - Atualizar seletores no código")
    print()
    print("3. Memória insuficiente:")
    print("   - Reduzir BATCH_SIZE")
    print("   - Processar em lotes menores")
    print()
    print("4. ChromeDriver issues:")
    print("   - Atualizar Chrome browser")
    print("   - pip install webdriver-manager")
    print()
    print("5. Anti-bot detection:")
    print("   - Aumentar delays entre ações")
    print("   - Usar user-agents diferentes")

def main():
    """Função principal do exemplo"""
    print("🎯 GodOfPrompt Scraper - Exemplos de Uso")
    print("=" * 60)

    exemplo_extracao_basica()
    exemplo_analise_resultados()
    exemplo_configuracao_personalizada()
    exemplo_tratamento_erros()

    print("\n" + "=" * 60)
    print("✨ Dicas Finais:")
    print("• Sempre teste com --test antes da extração completa")
    print("• Monitore os logs em extraction_log.txt")
    print("• Use ambiente virtual para isolamento")
    print("• Respeite os termos de serviço do GodOfPrompt.ai")
    print("• Faça backups dos dados extraídos")

if __name__ == "__main__":
    main()
