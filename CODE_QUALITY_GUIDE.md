# 🛡️ Guia de Qualidade de Código - GodOfPrompt Scraper

## 📋 Visão Geral

Este guia estabelece os padrões de qualidade de código para o projeto GodOfPrompt Scraper, integrando ferramentas automatizadas de linting, formatação e revisão de código.

## 🛠️ Ferramentas de Qualidade

### uv (Gerenciador de Pacotes)

#### Por que uv?
O **uv** é o gerenciador de pacotes Python mais rápido disponível, oferecendo:

- ⚡ **Performance excepcional**: Até 10x mais rápido que pip
- 🔄 **Gerenciamento automático**: Ambientes virtuais criados automaticamente
- 📦 **Resolução inteligente**: Algoritmos avançados para resolução de dependências
- 🔒 **Segurança**: Verificações de integridade e hash
- 💾 **Cache eficiente**: Reutilização inteligente de downloads

#### Instalação e Uso
```bash
# Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Criar ambiente virtual (automático)
uv venv

# Instalar dependências (ultrarrápido!)
uv pip install -r requirements.txt

# Sincronizar dependências
uv pip sync requirements.txt

# Listar dependências instaladas
uv pip list
```

#### Benefícios para Desenvolvimento
- **Setup mais rápido**: Projetos são configurados em segundos
- **Consistência**: Mesmo ambiente em diferentes máquinas
- **Isolamento**: Dependências completamente isoladas
- **Reprodutibilidade**: Environments idênticos garantidos

### CodeRabbit (Revisão Automática)
O projeto utiliza **CodeRabbit** para revisões automáticas de código com as seguintes configurações:

#### Configurações Principais (.coderabbit.yaml)
```yaml
language: "pt-BR"  # Revisões em português brasileiro
profile: "chill"   # Perfil relaxado
auto_review:
  enabled: true    # Revisões automáticas ativadas
  auto_incremental_review: true  # Revisões incrementais
```

#### Funcionalidades Ativadas
- ✅ **Resumos de alto nível** das mudanças
- ✅ **Estimativa de esforço** de revisão
- ✅ **Diagramas de sequência** para fluxos complexos
- ✅ **Avaliação de issues** relacionadas
- ✅ **Sugestões de labels** automáticas
- ✅ **Geração automática de títulos** para PRs
- ✅ **Poemas** criativos em revisões

### Ferramentas Python

#### Ruff (Linting e Formatação)
**Ruff** é a ferramenta principal de linting e formatação:

```bash
# Instalação
pip install ruff

# Verificação de código
ruff check .

# Formatação automática
ruff format .

# Correção automática de problemas
ruff check --fix .
```

#### Flake8 (Linting Estilo PEP 8)
**Flake8** complementa o Ruff com verificações específicas:

```bash
# Instalação
pip install flake8

# Verificação
flake8 . --max-line-length=88 --extend-ignore=E203,W503
```

#### Pylint (Análise Estática Avançada)
**Pylint** para análise mais profunda:

```bash
# Instalação
pip install pylint

# Análise
pylint extract_links.py exemplo_uso.py --disable=C0103,C0114,C0115,C0116
```

### Ferramentas de Segurança

#### Gitleaks (Detecção de Secrets)
**Gitleaks** verifica se não há credenciais vazadas:

```bash
# Instalação
brew install gitleaks  # macOS
# ou
pip install gitleaks

# Verificação
gitleaks detect -v
```

### Ferramentas de Documentação

#### LanguageTool (Correção Ortográfica)
**LanguageTool** para verificação de português em comentários e docstrings:

```bash
# Verificações ativadas no CodeRabbit
languagetool:
  enabled: true
  level: "default"
```

## 📏 Padrões de Código

### Estrutura de Arquivos Python

#### Imports Organizados
```python
# 1. Imports padrão da biblioteca
import logging
import time
from datetime import datetime

# 2. Imports de terceiros
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import yaml
import json

# 3. Imports locais
from my_module import MyClass
```

#### Funções com Docstrings Completas
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

    Example:
        >>> links = extract_links_from_page("https://example.com", "Teste")
        >>> print(f"Encontrados {len(links)} links")
    """
```

### Convenções de Nomenclatura

#### Variáveis e Funções
```python
# ✅ Correto
def extract_prompt_links(url, category_name):
    prompt_links = []
    max_retries = 3

# ❌ Incorreto
def extractPromptLinks(URL, categoryName):
    PROMPT_LINKS = []
    MAX_RETRIES = 3
```

#### Classes
```python
# ✅ Correto
class WebScraper:
    """Classe base para web scraping."""

# ❌ Incorreto
class web_scraper:
    """Classe base para web scraping."""
```

### Tratamento de Erros

#### Try-Except Estruturado
```python
def safe_web_request(url: str, timeout: int = 30) -> dict:
    """Faz requisição web com tratamento robusto de erros."""
    try:
        response = requests.get(url, timeout=timeout)
        response.raise_for_status()
        return {"success": True, "data": response.json()}
    except requests.Timeout:
        logging.error(f"Timeout na requisição para {url}")
        return {"success": False, "error": "timeout"}
    except requests.HTTPError as e:
        logging.error(f"Erro HTTP {e.response.status_code} para {url}")
        return {"success": False, "error": "http_error", "status_code": e.response.status_code}
    except requests.RequestException as e:
        logging.error(f"Erro de rede para {url}: {e}")
        return {"success": False, "error": "network_error"}
    except json.JSONDecodeError:
        logging.error(f"Resposta inválida (não JSON) para {url}")
        return {"success": False, "error": "invalid_json"}
    except Exception as e:
        logging.error(f"Erro inesperado para {url}: {e}")
        return {"success": False, "error": "unexpected_error"}
```

## 🔍 Análise Estática

### Configuração do Ruff
Crie um arquivo `pyproject.toml` na raiz do projeto:

```toml
[tool.ruff]
line-length = 88
target-version = "py38"

[tool.ruff.lint]
select = [
    "E",  # pycodestyle errors
    "W",  # pycodestyle warnings
    "F",  # pyflakes
    "I",  # isort
    "B",  # flake8-bugbear
    "C4", # flake8-comprehensions
    "UP", # pyupgrade
]

ignore = [
    "E203",  # whitespace before ':'
    "E501",  # line too long
    "W503",  # line break before binary operator
]

[tool.ruff.lint.isort]
known-first-party = ["godofprompt"]

[tool.ruff.format]
quote-style = "double"
indent-style = "space"
skip-magic-trailing-comma = false
line-ending = "auto"
```

### Configuração do Flake8
Arquivo `.flake8`:

```ini
[flake8]
max-line-length = 88
extend-ignore = E203, W503
exclude =
    .git,
    __pycache__,
    venv,
    .venv,
    build,
    dist,
    *.egg-info
per-file-ignores =
    __init__.py:F401
```

## 🧪 Testes Automatizados

### Estrutura de Testes
```
tests/
├── __init__.py
├── test_extract_links.py
├── test_login_automation.py
├── test_anti_blocking.py
└── conftest.py
```

### Exemplo de Teste
```python
import pytest
from unittest.mock import Mock, patch
from extract_links import extract_links_from_page

class TestExtractLinks:
    """Testes para a função extract_links_from_page."""

    @patch('extract_links.webdriver.Chrome')
    def test_extract_links_success(self, mock_chrome):
        """Testa extração bem-sucedida de links."""
        # Arrange
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver

        mock_driver.execute_script.return_value = [
            {"url": "https://example.com/prompt1", "name": "Prompt 1"},
            {"url": "https://example.com/prompt2", "name": "Prompt 2"}
        ]

        # Act
        result = extract_links_from_page("https://example.com", "Teste")

        # Assert
        assert len(result) == 2
        assert result[0]["name"] == "Prompt 1"
        assert "example.com" in result[0]["url"]

    @patch('extract_links.webdriver.Chrome')
    def test_extract_links_timeout(self, mock_chrome):
        """Testa tratamento de timeout."""
        # Arrange
        mock_driver = Mock()
        mock_chrome.return_value = mock_driver
        mock_driver.execute_script.side_effect = TimeoutException()

        # Act & Assert
        with pytest.raises(Exception):
            extract_links_from_page("https://example.com", "Teste")
```

### Execução de Testes
```bash
# Instalar pytest
pip install pytest pytest-cov

# Executar testes
pytest tests/

# Com cobertura
pytest --cov=godofprompt tests/ --cov-report=html

# Testes específicos
pytest tests/test_extract_links.py::TestExtractLinks::test_extract_links_success -v
```

## 📊 Métricas de Qualidade

### CodeRabbit Metrics
O CodeRabbit fornece métricas automáticas:

- **Taxa de docstrings**: > 80%
- **Complexidade ciclomática**: < 10
- **Cobertura de testes**: > 70%
- **Dívida técnica**: Monitorada automaticamente

### Métricas Personalizadas
```python
def calculate_code_metrics():
    """Calcula métricas de qualidade do código."""
    import radon.complexity as cc
    import radon.metrics as metrics

    # Complexidade ciclomática
    complexity = cc.average_complexity('extract_links.py')
    print(f"Complexidade média: {complexity}")

    # Métricas de manutenibilidade
    mi = metrics.mi_parameters('extract_links.py')
    print(f"Índice de manutenibilidade: {mi}")

    # Contagem de linhas
    with open('extract_links.py', 'r') as f:
        lines = f.readlines()
        code_lines = [line for line in lines if line.strip() and not line.strip().startswith('#')]
        print(f"Linhas de código: {len(code_lines)}")
        print(f"Total de linhas: {len(lines)}")
```

## 🚀 Integração CI/CD

### GitHub Actions Workflow
```yaml
name: Code Quality

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  quality:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.8'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install ruff flake8 pylint pytest pytest-cov

    - name: Run Ruff
      run: ruff check .

    - name: Run Flake8
      run: flake8 .

    - name: Run Pylint
      run: pylint extract_links.py --disable=C0103,C0114,C0115,C0116

    - name: Run tests
      run: pytest tests/ --cov=. --cov-report=xml

    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

### Pre-commit Hooks
Arquivo `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 22.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pycqa/flake8
    rev: 4.0.1
    hooks:
      - id: flake8

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v0.991
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

## 📈 Monitoramento Contínuo

### Dashboard de Qualidade
```python
class QualityDashboard:
    """Dashboard para monitoramento de qualidade de código."""

    def __init__(self):
        self.metrics = {}

    def collect_metrics(self):
        """Coleta métricas atuais."""
        # Ruff violations
        # Test coverage
        # Complexity metrics
        # Documentation coverage
        pass

    def generate_report(self):
        """Gera relatório de qualidade."""
        report = {
            'timestamp': datetime.now().isoformat(),
            'ruff_violations': self._count_ruff_violations(),
            'test_coverage': self._get_test_coverage(),
            'complexity_score': self._calculate_complexity(),
            'documentation_coverage': self._calculate_doc_coverage(),
            'recommendations': self._generate_recommendations()
        }
        return report

    def _generate_recommendations(self):
        """Gera recomendações baseadas nas métricas."""
        recommendations = []

        if self.metrics.get('ruff_violations', 0) > 10:
            recommendations.append("Executar 'ruff check --fix .' para corrigir violações")

        if self.metrics.get('test_coverage', 0) < 70:
            recommendations.append("Aumentar cobertura de testes para pelo menos 70%")

        if self.metrics.get('complexity_score', 0) > 8:
            recommendations.append("Refatorar funções com alta complexidade ciclomática")

        return recommendations
```

## 🎯 Melhores Práticas

### Checklist de Qualidade
- [ ] **Ruff**: `ruff check . && ruff format .`
- [ ] **Flake8**: `flake8 .`
- [ ] **Pylint**: `pylint *.py`
- [ ] **Testes**: `pytest tests/ --cov=.`
- [ ] **Docstrings**: Todas as funções públicas documentadas
- [ ] **Type hints**: Usar type hints quando possível
- [ ] **Logs**: Logging apropriado em todas as operações críticas

### Revisão de Código
- ✅ **Funcionalidade**: O código funciona como esperado?
- ✅ **Legibilidade**: O código é fácil de entender?
- ✅ **Manutenibilidade**: O código é fácil de modificar?
- ✅ **Performance**: O código é eficiente?
- ✅ **Segurança**: Não há vulnerabilidades óbvias?
- ✅ **Testes**: Há testes adequados?
- ✅ **Documentação**: O código está bem documentado?

### Padrões de Commit
```bash
# Formato recomendado
type(scope): description

# Exemplos
feat(scraper): adicionar extração de conteúdo completo
fix(login): corrigir timeout no login automático
docs(readme): atualizar guia de instalação
test(scraper): adicionar testes para função extract_links
refactor(anti-blocking): melhorar sistema de delays adaptativos
```

---

## 🏆 Resultado Esperado

Com essas ferramentas e práticas implementadas, o projeto GodOfPrompt Scraper terá:

- ✅ **Código consistente** seguindo PEP 8
- ✅ **Qualidade garantida** por ferramentas automatizadas
- ✅ **Revisões eficientes** com CodeRabbit
- ✅ **Testes abrangentes** com alta cobertura
- ✅ **Documentação completa** e atualizada
- ✅ **Manutenibilidade** simplificada
- ✅ **Colaboração** facilitada

**🎯 Meta**: Taxa de aprovação de 95% nas revisões automáticas e zero violações críticas de qualidade.
