#!/usr/bin/env python3
"""
Script completo para extrair TODOS os links dos prompts do godofprompt.ai
"""

import requests
from bs4 import BeautifulSoup
import yaml
import json
from urllib.parse import urlparse, parse_qs
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import logging
import os
from datetime import datetime

def setup_logging():
    """Configura o sistema de logging"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('extraction_log.txt'),
            logging.StreamHandler()
        ]
    )

def load_categories():
    """Carrega as categorias do arquivo links.yaml"""
    with open('links.yaml', 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)
    return data['categoriasDePrompt']

def create_driver():
    """Cria e configura o driver do Chrome"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    return webdriver.Chrome(options=chrome_options)

def wait_for_prompts_to_load(driver, timeout=30):
    """Aguarda o carregamento dos prompts na página"""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script("return document.querySelectorAll('[wized=\"plp_prompt_item_all\"]').length > 0")
        )
        time.sleep(2)  # Espera extra para garantir carregamento completo
        return True
    except Exception as e:
        logging.error(f"Erro aguardando carregamento dos prompts: {e}")
        return False

def extract_prompts_from_page(driver):
    """Extrai os prompts da página atual"""
    script = """
    return Array.from(document.querySelectorAll('[wized="plp_prompt_item_all"]')).map(el => {
        const linkElement = el.querySelector('[wized="plp_prompt_item_link"]');
        const nameElement = el.querySelector('[wized="plp_prompt_name"]');
        const idElement = el.querySelector('[wized="plp_prompt_id"]');

        return {
            url: linkElement ? linkElement.href : null,
            name: nameElement ? nameElement.textContent.trim() : '',
            id: idElement ? idElement.textContent.trim() : '',
            category: window.location.search.includes('category=') ?
                new URLSearchParams(window.location.search).get('category') : 'unknown'
        };
    });
    """

    try:
        prompts = driver.execute_script(script)
        valid_prompts = []

        for prompt in prompts:
            if prompt['url'] and prompt['url'] != '#':
                # Garantir URL absoluta
                if prompt['url'].startswith('/'):
                    prompt['url'] = f"https://www.godofprompt.ai{prompt['url']}"

                valid_prompts.append({
                    'url': prompt['url'],
                    'name': prompt['name'],
                    'id': prompt['id'],
                    'category': prompt['category']
                })

        return valid_prompts
    except Exception as e:
        logging.error(f"Erro extraindo prompts da página: {e}")
        return []

def get_pagination_info(driver):
    """Obtém informações sobre a paginação"""
    script = """
    const nextBtn = document.querySelector('[wized="pagin-next"]');
    const currentPageEl = document.querySelector('[wized="pagin-cur-page"]');
    const totalPagesEl = document.querySelector('[wized="pagin-all-pages"]');

    return {
        hasNext: nextBtn && !nextBtn.disabled && nextBtn.style.display !== 'none',
        currentPage: currentPageEl ? parseInt(currentPageEl.textContent) : 1,
        totalPages: totalPagesEl ? parseInt(totalPagesEl.textContent) : 1
    };
    """

    try:
        return driver.execute_script(script)
    except Exception as e:
        logging.error(f"Erro obtendo informações de paginação: {e}")
        return {'hasNext': False, 'currentPage': 1, 'totalPages': 1}

def click_next_page(driver):
    """Clica no botão 'próximo' para navegar para a próxima página"""
    try:
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, '[wized="pagin-next"]'))
        )
        next_button.click()
        time.sleep(3)  # Espera carregamento da nova página
        return True
    except Exception as e:
        logging.error(f"Erro clicando no botão próximo: {e}")
        return False

def extract_category_links(category, driver=None, should_close_driver=True):
    """Extrai todos os links de uma categoria específica"""
    logging.info(f"Iniciando extração da categoria: {category['nome']}")
    logging.info(f"Quantidade esperada: {category['quantidadeDePrompts']}")
    logging.info(f"URL base: {category['link']}")

    if driver is None:
        driver = create_driver()

    try:
        # Carregar página inicial da categoria
        logging.info(f"Carregando página inicial: {category['link']}")
        driver.get(category['link'])

        # Aguardar carregamento dos prompts
        if not wait_for_prompts_to_load(driver):
            logging.error(f"Não foi possível carregar prompts para {category['nome']}")
            return []

        # Extrair prompts da primeira página
        all_prompts = extract_prompts_from_page(driver)
        logging.info(f"Página 1: {len(all_prompts)} prompts encontrados")

        # Verificar paginação e extrair das próximas páginas
        pagination_info = get_pagination_info(driver)
        current_page = pagination_info['currentPage']
        total_pages = pagination_info['totalPages']

        logging.info(f"Paginação detectada: Página {current_page} de {total_pages}")

        # Limitar a 50 páginas por categoria para evitar loops infinitos
        max_pages = min(total_pages, 50)

        while current_page < max_pages and pagination_info['hasNext']:
            logging.info(f"Navegando para página {current_page + 1}...")

            if not click_next_page(driver):
                logging.error(f"Falha ao navegar para página {current_page + 1}")
                break

            # Aguardar carregamento da nova página
            if not wait_for_prompts_to_load(driver):
                logging.error(f"Falha no carregamento da página {current_page + 1}")
                break

            # Extrair prompts da nova página
            new_prompts = extract_prompts_from_page(driver)
            logging.info(f"Página {current_page + 1}: {len(new_prompts)} prompts encontrados")

            # Adicionar apenas prompts novos
            for prompt in new_prompts:
                if not any(p['url'] == prompt['url'] for p in all_prompts):
                    all_prompts.append(prompt)

            current_page += 1
            pagination_info = get_pagination_info(driver)

        logging.info(f"Extração concluída para {category['nome']}: {len(all_prompts)} prompts únicos")
        return all_prompts

    except Exception as e:
        logging.error(f"Erro durante extração da categoria {category['nome']}: {e}")
        return []
    finally:
        if should_close_driver and driver:
            driver.quit()

def save_links_to_yaml(all_data, filename="links_extraidos.yaml"):
    """Salva apenas os links em formato YAML estruturado"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_with_timestamp = f"{timestamp}_{filename}"

    # Estrutura simplificada para YAML
    yaml_data = {
        'metadata': {
            'data_extracao': datetime.now().isoformat(),
            'total_categorias': len(all_data),
            'total_prompts': sum(len(cat_data['prompts']) for cat_data in all_data.values())
        },
        'categorias': {}
    }

    for cat_name, cat_data in all_data.items():
        yaml_data['categorias'][cat_name] = {
            'quantidade_extraida': len(cat_data['prompts']),
            'quantidade_esperada': cat_data['quantidade_esperada'],
            'links': [prompt['url'] for prompt in cat_data['prompts']]
        }

    # Salvar arquivo YAML
    with open(filename_with_timestamp, 'w', encoding='utf-8') as f:
        yaml.dump(yaml_data, f, allow_unicode=True, default_flow_style=False, indent=2)

    logging.info(f"Links salvos em YAML: {filename_with_timestamp}")
    return filename_with_timestamp

def save_results(all_data, filename="todos_os_links.json"):
    """Salva os resultados em arquivo JSON"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename_with_timestamp = f"{timestamp}_{filename}"

    # Estatísticas gerais
    stats = {
        'data_extracao': datetime.now().isoformat(),
        'total_categorias': len(all_data),
        'total_prompts': sum(len(cat_data['prompts']) for cat_data in all_data.values()),
        'categorias': {}
    }

    for cat_name, cat_data in all_data.items():
        stats['categorias'][cat_name] = {
            'quantidade_extraida': len(cat_data['prompts']),
            'quantidade_esperada': cat_data['quantidade_esperada'],
            'url_base': cat_data['url_base']
        }

    # Estrutura final
    result = {
        'estatisticas': stats,
        'dados': all_data
    }

    # Salvar arquivo
    with open(filename_with_timestamp, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    logging.info(f"Resultados salvos em: {filename_with_timestamp}")
    return filename_with_timestamp

def extract_prompt_content(driver, prompt_url, prompt_name, category_name):
    """Extrai o conteúdo completo de um prompt individual"""
    try:
        logging.info(f"Extraindo conteúdo: {prompt_name}")
        driver.get(prompt_url)

        # Aguardar carregamento da página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        time.sleep(2)  # Aguardar carregamento dinâmico

        # Tentar diferentes seletores para o conteúdo do prompt
        content_selectors = [
            '[data-wized="prompt_content"]',
            '.prompt-content',
            '.content',
            'main',
            'article',
            '.prompt-text',
            '[class*="content"]',
            '[class*="prompt"]'
        ]

        prompt_content = ""
        for selector in content_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    # Pegar o elemento com mais texto
                    best_element = max(elements, key=lambda e: len(e.text.strip()))
                    if len(best_element.text.strip()) > len(prompt_content):
                        prompt_content = best_element.text.strip()
            except Exception:
                continue

        # Se não encontrou conteúdo específico, pegar o texto principal da página
        if not prompt_content:
            try:
                body = driver.find_element(By.TAG_NAME, "body")
                prompt_content = body.text.strip()
            except Exception:
                prompt_content = "Conteúdo não encontrado"

        return {
            'url': prompt_url,
            'name': prompt_name,
            'category': category_name,
            'content': prompt_content,
            'extracted_at': datetime.now().isoformat(),
            'content_length': len(prompt_content)
        }

    except Exception as e:
        logging.error(f"Erro extraindo conteúdo de {prompt_name}: {e}")
        return {
            'url': prompt_url,
            'name': prompt_name,
            'category': category_name,
            'content': f"Erro na extração: {str(e)}",
            'extracted_at': datetime.now().isoformat(),
            'content_length': 0
        }

def save_prompts_to_directory(all_data, base_dir="prompts_extraidos"):
    """Salva cada prompt em um arquivo separado em diretório organizado"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = f"{timestamp}_{base_dir}"

    # Criar diretórios
    os.makedirs(output_dir, exist_ok=True)

    # Estatísticas
    total_saved = 0
    categories_stats = {}

    # Salvar cada categoria em subdiretório
    for cat_name, cat_data in all_data.items():
        cat_dir = os.path.join(output_dir, cat_name.replace(" ", "_").lower())
        os.makedirs(cat_dir, exist_ok=True)

        category_saved = 0

        for i, prompt in enumerate(cat_data['prompts'], 1):
            # Nome do arquivo seguro
            safe_name = "".join(c for c in prompt['name'][:50] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(" ", "_").lower()
            if not safe_name:
                safe_name = f"prompt_{i}"

            filename = f"{i:03d}_{safe_name}.md"
            filepath = os.path.join(cat_dir, filename)

            # Conteúdo do arquivo
            content = f"""# {prompt['name']}

**Categoria:** {cat_name}
**URL:** {prompt['url']}
**ID:** {prompt.get('id', 'N/A')}
**Extraído em:** {datetime.now().isoformat()}

---

{prompt.get('content', 'Conteúdo não disponível')}

---

*Fonte: GodOfPrompt.ai*
"""

            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                category_saved += 1
                total_saved += 1
            except Exception as e:
                logging.error(f"Erro salvando {filepath}: {e}")

        categories_stats[cat_name] = category_saved
        logging.info(f"Categoria {cat_name}: {category_saved} prompts salvos")

    # Criar arquivo de índice
    index_content = f"""# Índice de Prompts Extraídos

**Data de Extração:** {datetime.now().isoformat()}
**Total de Prompts:** {total_saved}
**Diretório:** {output_dir}

## Estatísticas por Categoria

"""

    for cat_name, count in categories_stats.items():
        index_content += f"- **{cat_name}:** {count} prompts\n"

    index_content += "\n## Estrutura de Arquivos\n\n"
    index_content += "Cada categoria tem seu próprio subdiretório com arquivos Markdown individuais.\n"
    index_content += "Formato do arquivo: `NNN_nome_do_prompt.md`\n\n"
    index_content += "---\n\n*Gerado automaticamente pelo GodOfPrompt Scraper*"

    index_path = os.path.join(output_dir, "README.md")
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)

    logging.info(f"Prompts salvos no diretório: {output_dir}")
    logging.info(f"Total de arquivos criados: {total_saved}")
    return output_dir

def main():
    """Função principal para extrair todos os links"""
    print("🚀 === EXTRATOR COMPLETO DE LINKS DO GODOFPROMPT.AI ===\n")

    # Configurar logging
    setup_logging()
    logging.info("Iniciando extração completa de links")

    try:
        # Carregar categorias
        categories = load_categories()
        logging.info(f"Categorias encontradas: {len(categories)}")

        # Exibir informações das categorias
        print("\n📋 CATEGORIAS A SEREM EXTRAÍDAS:")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat['nome']}: {cat['quantidadeDePrompts']} prompts")
        print()

        # Perguntar se quer continuar
        continuar = input("Deseja continuar com a extração? (s/n): ").lower().strip()
        if continuar != 's':
            print("Extração cancelada.")
            return

        # Resultados finais
        all_data = {}

        # Criar driver único para reutilização
        driver = create_driver()

        try:
            # Processar cada categoria
            for i, category in enumerate(categories, 1):
                print(f"\n🔄 [{i}/{len(categories)}] Processando: {category['nome']}")

                # Extrair links da categoria
                prompts = extract_category_links(category, driver, should_close_driver=False)

                # Armazenar resultados
                all_data[category['nome']] = {
                    'quantidade_esperada': category['quantidadeDePrompts'],
                    'url_base': category['link'],
                    'prompts': prompts
                }

                # Exibir estatísticas da categoria
                print(f"✅ {category['nome']}: {len(prompts)}/{category['quantidadeDePrompts']} prompts extraídos")

                # Pequena pausa entre categorias
                time.sleep(2)

        finally:
            # Fechar driver
            if driver:
                driver.quit()

        # Salvar resultados
        print("\n💾 Salvando resultados...")

        # Salvar links em YAML (sempre)
        yaml_file = save_links_to_yaml(all_data)

        # Perguntar se quer extrair conteúdo completo dos prompts
        extrair_conteudo = input("\n🤔 Deseja extrair o conteúdo completo dos prompts? (s/n): ").lower().strip()

        prompts_dir = None
        if extrair_conteudo == 's':
            print("\n📝 Iniciando extração de conteúdo dos prompts...")
            print("⚠️  ATENÇÃO: Isso pode demorar muito tempo dependendo do número de prompts!")

            # Criar driver para extração de conteúdo
            content_driver = create_driver()

            try:
                # Extrair conteúdo de todos os prompts
                enriched_data = {}

                for cat_name, cat_data in all_data.items():
                    print(f"\n🔄 Processando conteúdo da categoria: {cat_name}")
                    enriched_prompts = []

                    for i, prompt in enumerate(cat_data['prompts'], 1):
                        if i % 10 == 0:  # Log a cada 10 prompts
                            print(f"  📄 Processado {i}/{len(cat_data['prompts'])} prompts de {cat_name}")

                        try:
                            # Extrair conteúdo completo
                            full_prompt = extract_prompt_content(
                                content_driver,
                                prompt['url'],
                                prompt['name'],
                                cat_name
                            )
                            enriched_prompts.append(full_prompt)

                            # Pequena pausa para não sobrecarregar
                            time.sleep(1)

                        except Exception as e:
                            logging.error(f"Erro no prompt {prompt['name']}: {e}")
                            # Manter dados originais se falhar
                            enriched_prompts.append({
                                **prompt,
                                'content': 'Erro na extração de conteúdo',
                                'content_length': 0
                            })

                    enriched_data[cat_name] = {
                        **cat_data,
                        'prompts': enriched_prompts
                    }

                # Salvar prompts completos em diretório
                prompts_dir = save_prompts_to_directory(enriched_data)
                print(f"\n✅ Prompts completos salvos em: {prompts_dir}")

            finally:
                content_driver.quit()

        # Salvar resultados completos em JSON (sempre)
        json_file = save_results(all_data)

        # Exibir estatísticas finais
        total_prompts = sum(len(cat_data['prompts']) for cat_data in all_data.values())
        total_esperado = sum(cat['quantidadeDePrompts'] for cat in categories)

        print("\n🎉 === EXTRAÇÃO CONCLUÍDA ===")
        print(f"📁 Links salvos em: {yaml_file}")
        print(f"📁 Dados completos salvos em: {json_file}")
        if prompts_dir:
            print(f"📁 Prompts completos salvos em: {prompts_dir}")
        print(f"📊 Total de prompts extraídos: {total_prompts}")
        print(f"🎯 Total esperado: {total_esperado}")
        print(f"📈 Taxa de sucesso geral: {(total_prompts / total_esperado) * 100:.1f}%")
        print("\n📈 Detalhes por categoria:")

        for cat_name, cat_data in all_data.items():
            porcentagem = (len(cat_data['prompts']) / cat_data['quantidade_esperada']) * 100
            print(f"  {cat_name}: {len(cat_data['prompts'])}/{cat_data['quantidade_esperada']} ({porcentagem:.1f}%)")

        logging.info("Extração completa finalizada com sucesso")

    except KeyboardInterrupt:
        print("\n⚠️  Extração interrompida pelo usuário")
        logging.warning("Extração interrompida pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro durante execução: {e}")
        logging.error(f"Erro durante execução: {e}")

def test_category(category_name=None):
    """Testa a extração de uma categoria específica"""
    print("🧪 === MODO DE TESTE ===\n")

    setup_logging()
    categories = load_categories()

    # Selecionar categoria
    if category_name:
        category = next((cat for cat in categories if cat['nome'] == category_name), None)
        if not category:
            print(f"❌ Categoria '{category_name}' não encontrada")
            return
    else:
        print("📋 Categorias disponíveis:")
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat['nome']}")

        try:
            choice = int(input("\nEscolha uma categoria (número): ")) - 1
            if 0 <= choice < len(categories):
                category = categories[choice]
            else:
                print("❌ Escolha inválida")
                return
        except ValueError:
            print("❌ Entrada inválida")
            return

    print(f"\n🔍 Testando categoria: {category['nome']}")
    print(f"📊 Esperado: {category['quantidadeDePrompts']} prompts")

    # Testar extração
    prompts = extract_category_links(category)

    print("\n✅ Teste concluído:")
    print(f"📊 Prompts extraídos: {len(prompts)}")
    print(f"🎯 Taxa de sucesso: {(len(prompts) / category['quantidadeDePrompts']) * 100:.1f}%")

    if prompts:
        print("\n📝 Primeiros 5 prompts:")
        for i, prompt in enumerate(prompts[:5], 1):
            print(f"  {i}. {prompt['name'][:50]}..." if len(prompt['name']) > 50 else f"  {i}. {prompt['name']}")
            print(f"     URL: {prompt['url']}")

        # Salvar resultados do teste
        print("\n💾 Salvando resultados do teste...")

        # Preparar dados para salvamento
        test_data = {
            category['nome']: {
                'quantidade_esperada': category['quantidadeDePrompts'],
                'url_base': category['link'],
                'prompts': prompts
            }
        }

        # Salvar links em YAML
        yaml_file = save_links_to_yaml(test_data, "teste_links.yaml")

        # Salvar dados completos em JSON
        json_file = save_results(test_data, "teste_dados.json")

        print(f"📁 Links salvos em: {yaml_file}")
        print(f"📁 Dados completos salvos em: {json_file}")

        # Perguntar se quer extrair conteúdo
        extrair_teste = input("\n🤔 Deseja testar extração de conteúdo de alguns prompts? (s/n): ").lower().strip()

        if extrair_teste == 's':
            print("\n📝 Testando extração de conteúdo...")

            # Pegar apenas os primeiros 3 prompts para teste
            test_prompts = prompts[:3]

            content_driver = create_driver()
            try:
                enriched_test_data = {}

                print("🔄 Extraindo conteúdo dos primeiros 3 prompts...")
                enriched_prompts = []

                for i, prompt in enumerate(test_prompts, 1):
                    print(f"  📄 Processando prompt {i}/3: {prompt['name'][:30]}...")

                    full_prompt = extract_prompt_content(
                        content_driver,
                        prompt['url'],
                        prompt['name'],
                        category['nome']
                    )
                    enriched_prompts.append(full_prompt)
                    time.sleep(1)

                enriched_test_data[category['nome']] = {
                    'quantidade_esperada': category['quantidadeDePrompts'],
                    'url_base': category['link'],
                    'prompts': enriched_prompts
                }

                # Salvar teste de conteúdo
                test_content_dir = save_prompts_to_directory(enriched_test_data, "teste_conteudo")
                print(f"✅ Conteúdo de teste salvo em: {test_content_dir}")

            finally:
                content_driver.quit()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        # Modo teste
        category_name = sys.argv[2] if len(sys.argv) > 2 else None
        test_category(category_name)
    else:
        # Modo completo
        main()
