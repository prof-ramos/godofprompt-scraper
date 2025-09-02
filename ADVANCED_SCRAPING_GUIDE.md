# 🚀 Guia Avançado de Scraping - GodOfPrompt.ai

## 📋 Visão Geral da Estratégia

Este guia documenta a estratégia completa para evitar bloqueios e otimizar performance no scraping do GodOfPrompt.ai, incluindo bypass de paywall e extração do conteúdo completo dos prompts.

### 🎯 Objetivos
1. **Evitar Bloqueios**: Técnicas avançadas de anti-detecção
2. **Otimizar Performance**: Scraping eficiente e controlado
3. **Bypass de Paywall**: Automação de login e sessão persistente
4. **Extração Completa**: Conteúdo detalhado de cada prompt
5. **Monitoramento**: Sistema adaptativo em tempo real

## 🛡️ Sistema Anti-Bloqueio

### 1. Anti-Detecção Avançada

#### Driver Configuration (`anti_blocking_strategy.py`)
```python
# User-Agents rotativos
user_agents = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36...",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36..."
]

# Dimensões de janela variáveis
width = random.randint(1366, 1920)
height = random.randint(768, 1080)

# Anti-detecção completa
chrome_options.add_argument("--disable-blink-features=AutomationControlled")
chrome_options.add_argument("--disable-images")  # Performance
chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
```

#### Delays Adaptativos
- **Base**: 2-8 segundos entre requisições
- **Adaptativo**: Aumenta após erros, diminui após sucessos
- **Jitter**: Aleatoriedade para mascarar padrões
- **Backoff Exponencial**: Delays progressivos após bloqueios

#### Circuit Breaker
- Pausa automática após 5 falhas consecutivas
- Timeout de recuperação: 5 minutos
- Proteção contra falhas em cascata

### 2. Técnicas de Bypass

#### Headers Realistas
```python
headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)...',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9...',
    'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
    'Accept-Encoding': 'gzip, deflate, br',
    'DNT': '1',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}
```

#### Comportamento Humano
- Scroll simulado para carregar conteúdo lazy-loaded
- Pausas variáveis entre ações
- Interações realistas com elementos
- Movimento de mouse simulado

## ⚡ Otimização de Performance

### 1. Processamento Paralelo (`performance_optimizer.py`)

#### Configuração Otimizada
```python
config = {
    'batch_size': 3,        # Lotes pequenos para controle
    'max_workers': 2,       # Concorrência conservadora
    'max_memory_mb': 1024,  # Limite de memória
    'use_cache': True,      # Cache inteligente
    'monitor_resources': True
}
```

#### Cache Inteligente
- Cache válido por 24 horas
- Máximo 50 categorias em cache
- Verificação automática de validade
- Limpeza inteligente de cache antigo

#### Monitoramento de Recursos
```python
# Limites automáticos
max_memory_mb = 1024
max_cpu_percent = 80

# Limpeza automática quando necessário
if memory_usage > threshold:
    gc.collect()
    time.sleep(5)
```

### 2. Métricas Detalhadas

#### Performance Tracking
- Prompts por segundo
- Páginas por minuto
- Taxa de sucesso por categoria
- Tempo médio de resposta
- Uso de recursos em tempo real

#### Relatórios Automáticos
- Estatísticas por categoria
- Identificação de gargalos
- Recomendações automáticas
- Estimativa de tempo restante

## 🔐 Sistema de Login Automático

### 1. Automação Robusta (`login_automation.py`)

#### Características
- **Múltiplas Tentativas**: Até 3 tentativas com backoff
- **Sessão Persistente**: Cache de cookies por 2 horas
- **Validação Contínua**: Teste automático de sessão
- **Fallback**: Modo headless após primeira tentativa

#### Detecção de Sucesso
```python
success_indicators = ['/dashboard', 'premium', 'logout', 'profile']
```

#### Sessão Reutilizável
```python
# Salva cookies e headers automaticamente
session_manager.save_session(cookies, headers)

# Recupera sessão válida
session = login_system.get_authenticated_session()
```

### 2. Bypass de Paywall

#### Estratégia
1. Login automático na primeira execução
2. Persistência de sessão entre execuções
3. Validação contínua durante scraping
4. Re-login automático se necessário

#### Validação de Sessão
```python
def test_session_validity(test_url):
    response = session.get(test_url)
    return 'signin' not in response.url
```

## 📊 Sistema de Monitoramento

### 1. Monitoramento em Tempo Real (`monitoring_system.py`)

#### Métricas Principais
- **Taxa de Sucesso**: Mínimo 70%
- **Tempo de Resposta**: Máximo 30s
- **Erros Consecutivos**: Máximo 5
- **Uso de Recursos**: CPU < 85%, RAM < 1GB

#### Alertas Automáticos
```python
alert_types = [
    'BLOQUEIO_DETECTADO',    # Keywords de bloqueio encontradas
    'ALTA_TAXA_ERRO',        # > 50% de erro
    'RESPOSTA_LENTA',        # > 30s de resposta
    'MEMORIA_ALTA'           # > limite de memória
]
```

### 2. Adaptação Automática

#### Controlador Adaptativo
- **Delay Dinâmico**: Ajuste baseado no status
- **Pausa Inteligente**: Para quando necessário
- **Troca de User-Agent**: Após múltiplas falhas
- **Recomendações**: Sugestões automáticas

#### Estados do Sistema
- `HEALTHY`: Funcionamento normal
- `WARNING`: Problemas menores detectados
- `CRITICAL`: Alta taxa de erro
- `BLOCKED`: Possível bloqueio detectado

## 🔍 Extração de Conteúdo Individual

### 1. Scraper de Prompts (`prompt_content_scraper.py`)

#### Estratégia Multi-Método
1. **Requests + BeautifulSoup**: Método rápido
2. **Selenium**: Fallback para conteúdo JavaScript
3. **FireCrawl**: Bypass profissional (opcional)

#### Extração Inteligente
```python
content_selectors = {
    'prompt_text': ['div[class*="prompt-text"]', 'pre', 'code'],
    'title': ['h1', 'h2', '.prompt-title'],
    'description': ['.description', '.prompt-description'],
    'tags': ['.tag', '.badge', '.chip']
}
```

#### Estrutura de Dados
```python
@dataclass
class PromptData:
    id: str
    title: str
    prompt_text: str
    description: str
    tags: List[str]
    category: str
    estimated_tokens: int
    extracted_at: str
    success: bool
```

### 2. Processamento em Paralelo

#### Configuração Segura
- **Max Workers**: 5 (conservador)
- **Batch Size**: 10 URLs por lote
- **Timeout**: 30s por URL
- **Retry**: Até 3 tentativas

#### Controle de Recursos
```python
# Pausas estratégicas
time.sleep(5)  # Entre lotes
time.sleep(1)  # Entre URLs individuais

# Monitoramento de memória
if memory_usage > 800MB:
    gc.collect()
```

## 🔥 Integração FireCrawl

### 1. Vantagens do FireCrawl (`firecrawl_integration.py`)

#### Recursos Avançados
- **Bypass Automático**: Anti-bot profissional
- **JavaScript Rendering**: Conteúdo dinâmico
- **Rate Limiting**: Automático
- **Formato Múltiplo**: HTML, Markdown, texto

#### Configuração Otimizada
```python
scrape_options = {
    'formats': ['markdown', 'html'],
    'onlyMainContent': True,
    'waitFor': 3000,  # 3s para JavaScript
    'actions': [
        {'type': 'wait', 'milliseconds': 2000},
        {'type': 'scroll', 'direction': 'down'},
        {'type': 'click', 'selector': '.modal-close', 'optional': True}
    ]
}
```

### 2. Scraper Híbrido

#### Estratégia Combinada
1. **FireCrawl**: URLs problemáticas
2. **Tradicional**: URLs simples
3. **Fallback Automático**: Se um método falha

#### Análise de Custo
- **FireCrawl**: ~$0.001 por URL
- **Tradicional**: Gratuito
- **Híbrido**: Melhor custo-benefício

## 📋 Fluxo de Execução Completo

### 1. Preparação
```bash
# Instalar dependências
pip install -r requirements.txt

# Configurar credenciais
export GODOFPROMPT_EMAIL="seu_email@exemplo.com"
export GODOFPROMPT_PASSWORD="sua_senha"
export FIRECRAWL_API_KEY="sua_api_key"  # Opcional
```

### 2. Execução Fase 1: Extração de Links
```python
# Extração otimizada de links
from performance_optimizer import OptimizedScraper

scraper = OptimizedScraper(config={
    'batch_size': 2,
    'max_workers': 2,
    'use_cache': True
})

links_data = scraper.extract_all_categories(categories, extract_func)
```

### 3. Execução Fase 2: Extração de Conteúdo
```python
# Setup do sistema completo
login_system = create_login_system(email, password)
monitor = SystemMonitor()
content_extractor = PromptContentExtractor(login_system, monitor)

# Login e extração
login_system.perform_login()
all_prompts = content_extractor.extract_multiple_prompts(all_links)
```

### 4. Monitoramento Contínuo
```python
# Sistema de monitoramento
monitoring_system = create_monitoring_system()
monitoring_system['start']()

# Adaptação automática
controller = AdaptiveController(monitor)
adaptive_delay = controller.get_adaptive_delay()
```

## 📈 Métricas de Sucesso

### 1. KPIs Principais
- **Taxa de Sucesso**: > 85%
- **Velocidade**: > 100 prompts/hora
- **Uptime**: > 95% sem bloqueios
- **Qualidade**: > 90% com conteúdo completo

### 2. Limites Operacionais
- **Requisições/Minuto**: < 60
- **Páginas/Categoria**: < 50
- **Concurrent Workers**: ≤ 5
- **Tempo/Prompt**: < 30s

## 🔧 Troubleshooting

### 1. Problemas Comuns

#### Bloqueios Detectados
```python
# Sinais de alerta
block_keywords = ['blocked', 'captcha', 'rate limit', 'access denied']

# Ações corretivas
- Aumentar delays (x4)
- Trocar User-Agent
- Pausar por 10 minutos
- Usar FireCrawl
```

#### Performance Baixa
```python
# Otimizações
- Reduzir max_workers para 2
- Aumentar batch delays para 10s
- Desabilitar imagens no Chrome
- Usar cache agressivamente
```

#### Falhas de Login
```python
# Soluções
- Verificar credenciais
- Usar modo não-headless
- Capturar screenshots
- Aumentar timeouts
```

### 2. Logs e Debug

#### Configuração de Logs
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('scraping.log'),
        logging.StreamHandler()
    ]
)
```

#### Debug Avançado
- Screenshots automáticos em falhas
- Dump de HTML para análise
- Métricas detalhadas por categoria
- Rastreamento de recursos

## 🎯 Recomendações Finais

### 1. Configuração Recomendada
```python
production_config = {
    'batch_size': 2,
    'max_workers': 2,
    'delays': {'min': 5, 'max': 15},
    'max_pages_per_category': 30,
    'use_cache': True,
    'monitor_resources': True,
    'session_timeout': 7200,  # 2 horas
    'max_retries': 3
}
```

### 2. Melhores Práticas
- **Começar Devagar**: Teste com 1-2 categorias
- **Monitorar Sempre**: Use sistema de alertas
- **Respeitar Limites**: Não sobrecarregar o servidor
- **Cache Inteligente**: Evitar re-processamento
- **Backup de Sessão**: Persistir estado

### 3. Expansão Futura
- **Proxy Rotation**: Para maior anonimato
- **Distributed Scraping**: Múltiplas IPs
- **ML-Based Adaptation**: Aprendizado automático
- **API Integration**: Usar APIs quando disponíveis

---

## 📊 Resumo de Arquivos

| Arquivo | Propósito | Funcionalidades Principais |
|---------|-----------|---------------------------|
| `anti_blocking_strategy.py` | Anti-detecção | User-agents rotativos, delays adaptativos, circuit breaker |
| `performance_optimizer.py` | Performance | Cache, processamento paralelo, métricas |
| `monitoring_system.py` | Monitoramento | Alertas, adaptação, dashboard |
| `login_automation.py` | Bypass paywall | Login automático, sessão persistente |
| `prompt_content_scraper.py` | Extração conteúdo | Multi-método, estrutura de dados |
| `firecrawl_integration.py` | Bypass profissional | FireCrawl, scraper híbrido |

---

**🎯 Resultado Esperado**: Sistema robusto capaz de extrair milhares de prompts com taxa de sucesso > 85% e sem bloqueios.