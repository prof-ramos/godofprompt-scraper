# 🚀 GodOfPrompt Scraper

> **Web scraper automatizado para extrair todos os links de prompts do GodOfPrompt.ai**

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.35+-green.svg)](https://selenium.dev/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 Descrição

Este projeto é um **web scraper inteligente** desenvolvido para extrair automaticamente todos os links dos prompts disponíveis no site [GodOfPrompt.ai](https://www.godofprompt.ai). O scraper utiliza técnicas avançadas de automação web para navegar pelas categorias e páginas de forma eficiente e respeitosa.

### ✨ Características Principais

- 🎯 **Extração Completa**: Captura todos os links de prompts de todas as categorias
- 🔄 **Navegação Automática**: Paginação automática com detecção inteligente
- 📊 **Relatórios Estruturados**: Saída em JSON com estatísticas detalhadas
- 🛡️ **Tratamento Robusto**: Logging avançado e tratamento de erros
- ⚡ **Performance Otimizada**: Processamento concorrente e cache inteligente
- 🎭 **Anti-detecção**: Técnicas para evitar bloqueios de bot

## 📁 Estrutura do Projeto

```
godofprompt-scraper/
├── extract_links.py          # Script principal de extração
├── exemplo_uso.py           # Exemplos de uso do scraper
├── links.yaml               # Configuração das categorias
├── requirements.txt         # Dependências Python
├── README.md               # Este arquivo
├── LICENSE                 # Licença MIT
├── .gitignore             # Arquivos ignorados pelo Git
├── .cursor/rules/          # Regras do Cursor IDE
│   ├── project-structure.mdc
│   ├── python-best-practices.mdc
│   ├── yaml-configuration.mdc
│   ├── web-scraping-selenium.mdc
│   ├── logging-error-handling.mdc
│   └── performance-optimization.mdc
├── venv/                   # Ambiente virtual
├── extraction_log.txt      # Logs da execução (gerado)
└── *.json                 # Arquivos de saída (gerados)
```

## 🚀 Instalação e Configuração

### Pré-requisitos

- **Python 3.8+**
- **Chrome Browser** (para Selenium)
- **Git** (opcional, para controle de versão)

### 1. Clone o Repositório

```bash
git clone https://github.com/seu-usuario/godofprompt-scraper.git
cd godofprompt-scraper
```

### 2. Configure o Ambiente Virtual

```bash
# Criar ambiente virtual
python3 -m venv venv

# Ativar ambiente virtual
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

**Dependências principais:**
- `selenium` - Automação web
- `beautifulsoup4` - Parsing HTML
- `pyyaml` - Processamento YAML
- `webdriver-manager` - Gerenciamento do ChromeDriver
- `requests` - HTTP requests

### 4. Verifique a Instalação

```bash
python3 extract_links.py --help
```

### 5. Execute Exemplos (Opcional)

Para ver exemplos de uso do scraper:

```bash
python3 exemplo_uso.py
```

## 🎯 Como Usar

### Modos de Execução

#### 🧪 Modo Teste (Recomendado)
Teste uma categoria específica antes da extração completa:

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Testar categoria específica
python3 extract_links.py --test "Marketing"

# Ou escolher categoria interativamente
python3 extract_links.py --test
```

#### 🚀 Modo Completo
Extraia todas as categorias automaticamente:

```bash
# Ativar ambiente virtual
source venv/bin/activate

# Executar extração completa
python3 extract_links.py
```

### 📊 Categorias Disponíveis

| Categoria | Prompts Esperados | Descrição |
|-----------|------------------|-----------|
| Vendas | 252 | Prompts para vendas e conversão |
| Educação | 276 | Prompts educacionais |
| Empreendedores Individuais | 201 | Para solopreneurs |
| SEO | 223 | Otimização para motores de busca |
| Produtividade | 218 | Aumento de produtividade |
| Escrita | 383 | Prompts de escrita criativa |
| Negócios | 293 | Estratégias de negócio |
| Marketing | 177 | Estratégias de marketing |

## 📋 Arquivos de Saída

### Formato JSON Estruturado

```json
{
  "estatisticas": {
    "data_extracao": "2024-09-02T18:53:47.434Z",
    "total_categorias": 8,
    "total_prompts": 2023,
    "categorias": {
      "Vendas": {
        "quantidade_extraida": 252,
        "quantidade_esperada": 252,
        "url_base": "https://www.godofprompt.ai/prompts?category=sales&premium=true"
      }
    }
  },
  "dados": {
    "Vendas": {
      "quantidade_esperada": 252,
      "url_base": "...",
      "prompts": [
        {
          "url": "https://www.godofprompt.ai/prompt?prompt=example-prompt",
          "name": "Example Prompt Title",
          "id": "example-prompt",
          "category": "sales"
        }
      ]
    }
  }
}
```

### Logs Detalhados

O arquivo `extraction_log.txt` contém logs detalhados da execução:

```
2024-09-02 18:53:47,434 - INFO - Iniciando extração completa de links
2024-09-02 18:53:49,102 - INFO - Iniciando extração da categoria: Vendas
2024-09-02 18:53:49,102 - INFO - Quantidade esperada: 252
2024-09-02 18:54:00,001 - INFO - Página 1: 12 prompts encontrados
2024-09-02 18:54:05,234 - INFO - Extração concluída para Vendas: 252 prompts únicos
```

## ⚙️ Configuração Avançada

### Personalizando Categorias

Edite o arquivo `links.yaml` para adicionar/modificar categorias:

```yaml
categoriasDePrompt:
  - nome: "Nova Categoria"
    quantidadeDePrompts: 150
    link: "https://www.godofprompt.ai/prompts?category=nova-categoria&premium=true"
```

### Configurações de Performance

```python
# Em extract_links.py, você pode ajustar:

# Número máximo de workers para processamento concorrente
MAX_WORKERS = 4

# Timeout para carregamento de páginas (segundos)
PAGE_LOAD_TIMEOUT = 30

# Máximo de páginas por categoria
MAX_PAGES_PER_CATEGORY = 50

# Delay entre requests (segundos)
REQUEST_DELAY = 2
```

## 🔧 Solução de Problemas

### Problema: ChromeDriver não encontrado

```bash
# Instalar ChromeDriver manualmente
pip install webdriver-manager
```

### Problema: Site lento ou timeout

```python
# Aumentar timeouts no código
WebDriverWait(driver, 60).until(...)  # 60 segundos
```

### Problema: Memória insuficiente

```python
# Processar em lotes menores
BATCH_SIZE = 50  # Reduzir de 100 para 50
```

### Problema: Anti-bot detection

```python
# Adicionar delays maiores
time.sleep(5)  # Aumentar delay entre ações
```

## 📊 Monitoramento e Estatísticas

### Métricas Principais

- **Taxa de Sucesso**: Prompts extraídos vs esperados
- **Tempo de Execução**: Por categoria e total
- **Taxa de Erro**: Falhas por categoria
- **Performance**: Prompts/segundo

### Relatórios Automáticos

O script gera automaticamente:
- Arquivo JSON com todos os dados extraídos
- Arquivo de log com detalhes da execução
- Estatísticas de performance por categoria

## 🤝 Contribuição

### Como Contribuir

1. **Fork** o projeto
2. **Clone** sua fork: `git clone https://github.com/seu-usuario/godofprompt-scraper.git`
3. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
4. **Commit** suas mudanças: `git commit -am 'Adiciona nova funcionalidade'`
5. **Push** para a branch: `git push origin feature/nova-funcionalidade`
6. **Abra** um Pull Request

### Diretrizes de Contribuição

- ✅ Seguir PEP 8 para código Python
- ✅ Adicionar testes para novas funcionalidades
- ✅ Atualizar documentação
- ✅ Usar commits descritivos
- ✅ Manter compatibilidade com Python 3.8+

## 📜 Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

## ⚠️ Avisos Legais

### Uso Ético
- ✅ Respeitar `robots.txt` do site
- ✅ Não sobrecarregar os servidores
- ✅ Usar apenas para fins educacionais/pesquisa
- ✅ Respeitar termos de serviço do GodOfPrompt.ai

### Responsabilidade
- ❌ Não usar para fins comerciais sem autorização
- ❌ Não distribuir dados extraídos sem permissão
- ❌ Não violar leis de propriedade intelectual

## 🆘 Suporte

### Como Obter Ajuda

1. **Verifique os logs**: Arquivo `extraction_log.txt`
2. **Execute modo teste**: `python3 extract_links.py --test`
3. **Verifique dependências**: `pip list`
4. **Abra uma issue**: [GitHub Issues](https://github.com/seu-usuario/godofprompt-scraper/issues)

### Problemas Comuns

| Problema | Solução |
|----------|---------|
| `ModuleNotFoundError` | Execute `pip install -r requirements.txt` |
| `WebDriverException` | Atualize Chrome browser |
| `TimeoutException` | Aumente `PAGE_LOAD_TIMEOUT` |
| `MemoryError` | Reduza `BATCH_SIZE` |

## 🗺️ Roadmap

### Próximas Funcionalidades

- [ ] 🖥️ **Interface Gráfica** - GUI para facilitar uso
- [ ] 📊 **Dashboard** - Visualização de estatísticas em tempo real
- [ ] 🔄 **API REST** - Interface programática para integração
- [ ] 📱 **Notificações** - Alertas por email/telegram
- [ ] ☁️ **Cloud Storage** - Integração com AWS S3/Google Cloud
- [ ] 🤖 **Auto-update** - Detecção automática de novas categorias
- [ ] 📈 **Analytics** - Análise avançada dos dados extraídos

### Melhorias Planejadas

- [ ] ⚡ **Performance** - Otimizações para grandes volumes
- [ ] 🛡️ **Robustez** - Melhor tratamento de erros
- [ ] 🔍 **Monitoramento** - Métricas avançadas de performance
- [ ] 📚 **Documentação** - Guias detalhados de uso

---

## 🙏 Agradecimentos

- [GodOfPrompt.ai](https://www.godofprompt.ai) - Pela plataforma incrível de prompts
- [Selenium](https://selenium.dev/) - Framework de automação web
- [Beautiful Soup](https://beautiful-soup-4.readthedocs.io/) - Biblioteca de parsing HTML
- Comunidade Python - Pelo ecossistema rico de bibliotecas

---

**⭐ Star este repositório se foi útil para você!**

**📧 Contato**: [seu-email@exemplo.com](mailto:seu-email@exemplo.com)

## 🛡️ Qualidade de Código

### Ferramentas Automatizadas

O projeto utiliza **CodeRabbit** para revisões automáticas e várias ferramentas de qualidade:

#### CodeRabbit (.coderabbit.yaml)
- ✅ **Revisões automáticas** em português brasileiro
- ✅ **Perfil relaxado** para desenvolvimento ágil
- ✅ **Estimativa de esforço** de revisão
- ✅ **Geração automática** de títulos e resumos

#### Ferramentas de Linting Python
```bash
# Ruff (Linting + Formatação)
pip install ruff
ruff check . && ruff format .

# Flake8 (PEP 8)
pip install flake8
flake8 .

# Pylint (Análise avançada)
pip install pylint
pylint *.py
```

#### Segurança
```bash
# Gitleaks (Detecção de secrets)
brew install gitleaks
gitleaks detect -v
```

### Padrões de Qualidade

#### Code Style
- ✅ **PEP 8** compliance automática com Ruff
- ✅ **Type hints** quando apropriado
- ✅ **Docstrings** completas em português
- ✅ **Imports organizados** (padrão → terceiros → locais)

#### Estrutura de Funções
```python
def extract_links_from_page(url: str, category_name: str) -> list:
    """
    Extrai links de uma página específica usando Selenium.

    Args:
        url: URL da página a ser analisada
        category_name: Nome da categoria para logging

    Returns:
        Lista de dicionários com links extraídos

    Raises:
        Exception: Quando há erro na extração
    """
```

#### Tratamento de Erros Robusto
```python
try:
    # Operação crítica
    result = perform_operation()
except SpecificException as e:
    logging.error(f"Erro específico: {e}")
    handle_specific_error()
except Exception as e:
    logging.error(f"Erro inesperado: {e}")
    handle_generic_error()
finally:
    # Limpeza obrigatória
    cleanup_resources()
```

### Métricas de Qualidade

- 📊 **Taxa de docstrings**: > 80%
- 🧪 **Cobertura de testes**: > 70%
- 🔄 **Complexidade ciclomática**: < 10
- 🚫 **Violações de linting**: 0 críticas

---

## 📚 Referências e Links

### Documentação
- [Selenium Documentation](https://selenium.dev/documentation/)
- [Python Best Practices](https://python-guide.org/)
- [Web Scraping Ethics](https://blog.apify.com/web-scraping-ethics/)

### Ferramentas
- [CodeRabbit](https://coderabbit.ai/) - Revisões automáticas
- [Ruff](https://beta.ruff.rs/docs/) - Linting ultrarrápido
- [GodOfPrompt.ai](https://www.godofprompt.ai/) - Plataforma de prompts

### Guias do Projeto
- [Guia de Scraping Avançado](ADVANCED_SCRAPING_GUIDE.md)
- [Guia de Qualidade de Código](CODE_QUALITY_GUIDE.md)
- [Regras do Cursor IDE](.cursor/rules/)

---

## 🤝 Como Contribuir

### Processo de Desenvolvimento

1. **Fork** o repositório
2. **Clone** sua fork: `git clone https://github.com/seu-usuario/godofprompt-scraper.git`
3. **Crie** uma branch: `git checkout -b feature/nova-funcionalidade`
4. **Desenvolva** seguindo os padrões de qualidade
5. **Teste** suas mudanças: `pytest tests/`
6. **Commit** com mensagem descritiva
7. **Push** para sua branch
8. **Abra** um Pull Request

### Requisitos para Contribuição

- ✅ Código passa em todas as verificações de qualidade
- ✅ Testes incluídos para novas funcionalidades
- ✅ Documentação atualizada
- ✅ Revisão do CodeRabbit aprovada
- ✅ Compatibilidade com Python 3.8+

### Labels de Pull Request

- `🚀 feature` - Nova funcionalidade
- `🐛 bugfix` - Correção de bug
- `📚 documentation` - Atualização de docs
- `🛡️ security` - Melhorias de segurança
- `⚡ performance` - Otimizações
- `🔄 refactor` - Refatoração de código

---

## 📈 Roadmap

### Próximas Funcionalidades (Q4 2024)

- [ ] 🖥️ **Interface Gráfica** - GUI para facilitar uso
- [ ] 📊 **Dashboard Web** - Visualização em tempo real
- [ ] 🔄 **API REST** - Interface programática
- [ ] 📱 **Notificações** - Alertas automáticos
- [ ] ☁️ **Cloud Integration** - AWS S3, Google Cloud
- [ ] 🤖 **Auto-Updates** - Detecção de novas categorias
- [ ] 📈 **Analytics Avançado** - ML para análise de prompts

### Melhorias Planejadas

- [ ] ⚡ **Performance** - Otimizações para milhões de prompts
- [ ] 🛡️ **Robustez** - Sistema de recuperação automática
- [ ] 🔍 **Monitoramento** - Métricas avançadas em tempo real
- [ ] 📚 **Documentação** - Tutoriais em vídeo
- [ ] 🌐 **Internacionalização** - Suporte a múltiplos idiomas

---

## ⚖️ Licença

Este projeto está licenciado sob a **MIT License** - veja o arquivo [LICENSE](LICENSE) para detalhes.

### Uso Ético
- ✅ Respeitar `robots.txt` do GodOfPrompt.ai
- ✅ Não sobrecarregar os servidores
- ✅ Usar apenas para fins educacionais/pesquisa
- ✅ Respeitar termos de serviço

### Responsabilidade
- ❌ Não usar para fins comerciais sem autorização
- ❌ Não distribuir dados extraídos sem permissão
- ❌ Não violar leis de propriedade intelectual

---

## 🆘 Suporte

### Canais de Suporte

1. **GitHub Issues**: [Problemas e Sugestões](https://github.com/seu-usuario/godofprompt-scraper/issues)
2. **Discussions**: [Perguntas Gerais](https://github.com/seu-usuario/godofprompt-scraper/discussions)
3. **Wiki**: [Documentação Completa](https://github.com/seu-usuario/godofprompt-scraper/wiki)

### Problemas Frequentes

| Problema | Solução |
|----------|---------|
| `ChromeDriver not found` | `pip install webdriver-manager` |
| `Timeout errors` | Aumentar `PAGE_LOAD_TIMEOUT` |
| `Memory issues` | Reduzir `BATCH_SIZE` |
| `Anti-bot detection` | Configurar delays maiores |

### Debug Mode
```bash
# Executar com debug detalhado
export DEBUG=1
python3 extract_links.py --test "Categoria" --verbose
```

---

## 🙏 Agradecimentos

### Comunidade e Colaboradores
- **GodOfPrompt.ai** - Pela incrível plataforma de prompts
- **Selenium Team** - Framework de automação web
- **Python Community** - Ecossistema rico de bibliotecas
- **Open Source Community** - Ferramentas e bibliotecas utilizadas

### Ferramentas e Serviços
- [CodeRabbit](https://coderabbit.ai/) - Revisões automáticas de código
- [GitHub](https://github.com/) - Plataforma de desenvolvimento
- [Ruff](https://beta.ruff.rs/) - Linting ultrarrápido
- [Cursor IDE](https://cursor.sh/) - Ambiente de desenvolvimento

---

## 🎯 Visão de Futuro

O **GodOfPrompt Scraper** tem como objetivo se tornar a ferramenta de referência para extração ética e eficiente de dados de plataformas de IA, combinando:

- **🏆 Excelência Técnica**: Algoritmos avançados e otimizações de performance
- **🛡️ Ética e Segurança**: Respeito total às leis e termos de serviço
- **🌍 Acessibilidade**: Interface intuitiva para usuários de todos os níveis
- **📊 Transparência**: Monitoramento completo e relatórios detalhados
- **🔄 Sustentabilidade**: Arquitetura escalável e manutenção simplificada

---

**⭐ Star este repositório se foi útil para você!**

**📧 Contato**: [seu-email@exemplo.com](mailto:seu-email@exemplo.com)

---

*Última atualização: Setembro 2024*