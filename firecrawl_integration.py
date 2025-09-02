#!/usr/bin/env python3
"""
Integração com FireCrawl para scraping avançado do GodOfPrompt.ai
FireCrawl oferece scraping mais robusto com bypass automático de anti-bot
"""

import time
import json
import logging
import os
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
import requests
from urllib.parse import urljoin, urlparse

try:
    from firecrawl import FirecrawlApp
    FIRECRAWL_AVAILABLE = True
except ImportError:
    FIRECRAWL_AVAILABLE = False
    logging.warning("FireCrawl não está instalado. Use: pip install firecrawl-py")


@dataclass
class FireCrawlConfig:
    """Configuração para FireCrawl"""
    
    # API Key (deve ser configurada via variável de ambiente)
    api_key: str = ""
    
    # Configurações de scraping
    formats: List[str] = field(default_factory=lambda: ["markdown", "html"])
    only_main_content: bool = True
    include_tags: List[str] = field(default_factory=lambda: ["h1", "h2", "h3", "p", "pre", "code", "div"])
    exclude_tags: List[str] = field(default_factory=lambda: ["script", "style", "nav", "footer", "header"])
    
    # Configurações de crawler
    wait_for: int = 3000  # ms
    timeout: int = 30000  # ms
    
    # Rate limiting
    max_requests_per_minute: int = 60
    
    def __post_init__(self):
        if not self.api_key:
            self.api_key = os.getenv('FIRECRAWL_API_KEY', '')
        
        if not self.api_key:
            logging.warning("FIRECRAWL_API_KEY não configurada")


class FireCrawlScraper:
    """Scraper usando FireCrawl para bypass avançado de anti-bot"""
    
    def __init__(self, config: FireCrawlConfig = None):
        if not FIRECRAWL_AVAILABLE:
            raise ImportError("FireCrawl não está disponível. Instale com: pip install firecrawl-py")
        
        self.config = config or FireCrawlConfig()
        
        if not self.config.api_key:
            raise ValueError("API key do FireCrawl é obrigatória")
        
        # Inicializar cliente FireCrawl
        self.app = FirecrawlApp(api_key=self.config.api_key)
        
        # Controle de rate limiting
        self.request_times = []
        self.last_request_time = 0
        
        # Estatísticas
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_cost': 0.0  # FireCrawl é pago
        }
    
    def scrape_single_url(self, url: str, custom_options: Dict = None) -> Dict[str, Any]:
        """Scraping de uma única URL com FireCrawl"""
        
        # Rate limiting
        self._enforce_rate_limit()
        
        # Opções de scraping
        scrape_options = {
            'formats': self.config.formats,
            'onlyMainContent': self.config.only_main_content,
            'includeTags': self.config.include_tags,
            'excludeTags': self.config.exclude_tags,
            'waitFor': self.config.wait_for,
            'timeout': self.config.timeout,
            'actions': [
                # Aguardar carregamento completo
                {'type': 'wait', 'milliseconds': 2000},
                
                # Simular scroll para carregar conteúdo lazy-loaded
                {'type': 'scroll', 'direction': 'down'},
                {'type': 'wait', 'milliseconds': 1000},
                
                # Tentar fechar modals/popups
                {'type': 'click', 'selector': 'button[aria-label="Close"]', 'optional': True},
                {'type': 'click', 'selector': '.modal-close', 'optional': True},
            ]
        }
        
        # Sobrescrever com opções customizadas
        if custom_options:
            scrape_options.update(custom_options)
        
        try:
            logging.info(f"Fazendo scraping com FireCrawl: {url}")
            
            # Executar scraping
            result = self.app.scrape_url(url, scrape_options)
            
            # Atualizar estatísticas
            self.stats['total_requests'] += 1
            self.stats['successful_requests'] += 1
            
            # Estimar custo (FireCrawl cobra por requisição)
            self.stats['total_cost'] += 0.001  # Estimativa
            
            # Processar resultado
            processed_result = self._process_firecrawl_result(result, url)
            
            logging.info(f"✅ Scraping bem-sucedido: {url}")
            return processed_result
            
        except Exception as e:
            self.stats['total_requests'] += 1
            self.stats['failed_requests'] += 1
            
            logging.error(f"❌ Erro no FireCrawl para {url}: {e}")
            
            return {
                'success': False,
                'url': url,
                'error': str(e),
                'content': {},
                'metadata': {}
            }
    
    def scrape_multiple_urls(self, urls: List[str], 
                           custom_options: Dict = None,
                           batch_size: int = 10) -> List[Dict[str, Any]]:
        """Scraping de múltiplas URLs com controle de lote"""
        
        logging.info(f"Iniciando scraping de {len(urls)} URLs com FireCrawl")
        
        results = []
        
        # Processar em lotes para controlar custos e rate limits
        for i in range(0, len(urls), batch_size):
            batch = urls[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(urls) - 1) // batch_size + 1
            
            logging.info(f"Processando lote {batch_num}/{total_batches} - {len(batch)} URLs")
            
            # Processar cada URL do lote
            for url in batch:
                result = self.scrape_single_url(url, custom_options)
                results.append(result)
                
                # Pequena pausa entre URLs
                time.sleep(1)
            
            # Pausa maior entre lotes
            if i + batch_size < len(urls):
                logging.info(f"Pausando entre lotes... (Custo estimado: ${self.stats['total_cost']:.3f})")
                time.sleep(5)
        
        logging.info(f"Scraping completo: {len(results)} URLs processadas")
        self._log_statistics()
        
        return results
    
    def scrape_with_crawl_mode(self, base_url: str, max_pages: int = 50) -> Dict[str, Any]:
        """Usa modo crawl do FireCrawl para descobrir e scraping automático"""
        
        crawl_options = {
            'limit': max_pages,
            'scrapeOptions': {
                'formats': self.config.formats,
                'onlyMainContent': self.config.only_main_content,
                'includeTags': self.config.include_tags,
                'excludeTags': self.config.exclude_tags
            },
            'crawlerOptions': {
                'includes': [
                    f"{base_url}/prompt/*",
                    f"{base_url}/prompts/*"
                ],
                'excludes': [
                    f"{base_url}/auth/*",
                    f"{base_url}/login*",
                    f"{base_url}/signup*"
                ]
            }
        }
        
        try:
            logging.info(f"Iniciando crawl do FireCrawl: {base_url}")
            
            # Iniciar crawl
            crawl_result = self.app.crawl_url(base_url, crawl_options)
            
            if crawl_result.get('success'):
                pages_data = crawl_result.get('data', [])
                
                logging.info(f"✅ Crawl bem-sucedido: {len(pages_data)} páginas descobertas")
                
                return {
                    'success': True,
                    'base_url': base_url,
                    'total_pages': len(pages_data),
                    'pages': pages_data,
                    'cost_estimate': len(pages_data) * 0.001
                }
            else:
                return {
                    'success': False,
                    'error': crawl_result.get('error', 'Crawl falhou'),
                    'base_url': base_url
                }
                
        except Exception as e:
            logging.error(f"Erro no crawl: {e}")
            return {
                'success': False,
                'error': str(e),
                'base_url': base_url
            }
    
    def _process_firecrawl_result(self, result: Dict, url: str) -> Dict[str, Any]:
        """Processa resultado do FireCrawl para formato padronizado"""
        
        if not result.get('success', False):
            return {
                'success': False,
                'url': url,
                'error': result.get('error', 'Scraping falhou'),
                'content': {},
                'metadata': {}
            }
        
        data = result.get('data', {})
        
        # Extrair conteúdos
        content = {
            'markdown': data.get('markdown', ''),
            'html': data.get('html', ''),
            'text': data.get('content', ''),  # Texto limpo
            'title': data.get('metadata', {}).get('title', ''),
            'description': data.get('metadata', {}).get('description', ''),
        }
        
        # Metadados
        metadata = data.get('metadata', {})
        metadata.update({
            'url': url,
            'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'scraping_method': 'firecrawl',
            'response_time': result.get('responseTime', 0),
            'status_code': metadata.get('statusCode', 0)
        })
        
        return {
            'success': True,
            'url': url,
            'content': content,
            'metadata': metadata,
            'raw_result': data  # Para debugging
        }
    
    def _enforce_rate_limit(self):
        """Controla rate limiting"""
        current_time = time.time()
        
        # Limpar requisições antigas (mais de 1 minuto)
        self.request_times = [t for t in self.request_times 
                             if current_time - t < 60]
        
        # Verificar se excedeu limite
        if len(self.request_times) >= self.config.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.request_times[0])
            if sleep_time > 0:
                logging.info(f"Rate limit atingido, aguardando {sleep_time:.1f}s")
                time.sleep(sleep_time)
        
        # Registrar requisição
        self.request_times.append(current_time)
        self.last_request_time = current_time
    
    def _log_statistics(self):
        """Log das estatísticas de uso"""
        success_rate = (self.stats['successful_requests'] / 
                       max(self.stats['total_requests'], 1)) * 100
        
        logging.info(f"""
        📊 Estatísticas FireCrawl:
        • Total de requisições: {self.stats['total_requests']}
        • Sucessos: {self.stats['successful_requests']}
        • Falhas: {self.stats['failed_requests']}
        • Taxa de sucesso: {success_rate:.1f}%
        • Custo estimado: ${self.stats['total_cost']:.3f}
        """)
    
    def get_usage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas de uso"""
        return dict(self.stats)


class HybridScraper:
    """Scraper híbrido que combina FireCrawl com métodos tradicionais"""
    
    def __init__(self, firecrawl_config: FireCrawlConfig = None, 
                 use_firecrawl_first: bool = True):
        self.use_firecrawl_first = use_firecrawl_first
        self.firecrawl_scraper = None
        
        # Tentar inicializar FireCrawl
        if FIRECRAWL_AVAILABLE and firecrawl_config and firecrawl_config.api_key:
            try:
                self.firecrawl_scraper = FireCrawlScraper(firecrawl_config)
                logging.info("FireCrawl inicializado com sucesso")
            except Exception as e:
                logging.warning(f"Falha ao inicializar FireCrawl: {e}")
        
        # Fallback para métodos tradicionais
        from prompt_content_scraper import PromptContentExtractor
        self.traditional_scraper = PromptContentExtractor()
    
    def scrape_url(self, url: str, prefer_firecrawl: bool = None) -> Dict[str, Any]:
        """Scraping híbrido com fallback automático"""
        
        if prefer_firecrawl is None:
            prefer_firecrawl = self.use_firecrawl_first
        
        # Método 1: FireCrawl (se disponível e preferido)
        if prefer_firecrawl and self.firecrawl_scraper:
            try:
                result = self.firecrawl_scraper.scrape_single_url(url)
                
                if result['success'] and result['content'].get('text'):
                    logging.info(f"✅ Sucesso com FireCrawl: {url}")
                    return result
                else:
                    logging.warning(f"FireCrawl retornou pouco conteúdo para: {url}")
                    
            except Exception as e:
                logging.error(f"Erro no FireCrawl: {e}")
        
        # Método 2: Scraper tradicional (fallback)
        logging.info(f"Usando método tradicional para: {url}")
        
        try:
            # Extrair apenas o ID da URL para o método tradicional
            url_parts = url.split('/')
            prompt_id = url_parts[-1] if url_parts else 'unknown'
            
            traditional_result = self.traditional_scraper.extract_single_prompt(
                url, prompt_id, "unknown"
            )
            
            # Converter para formato compatível
            return {
                'success': traditional_result.success,
                'url': url,
                'content': {
                    'text': traditional_result.prompt_text,
                    'title': traditional_result.title,
                    'description': traditional_result.description,
                    'markdown': traditional_result.prompt_text,
                    'html': traditional_result.raw_html
                },
                'metadata': {
                    'url': url,
                    'scraping_method': 'traditional',
                    'scraped_at': traditional_result.extracted_at,
                    'tags': traditional_result.tags,
                    'category': traditional_result.category
                },
                'error': traditional_result.error_message if not traditional_result.success else None
            }
            
        except Exception as e:
            logging.error(f"Erro no método tradicional: {e}")
            
            return {
                'success': False,
                'url': url,
                'error': f"Todos os métodos falharam: {str(e)}",
                'content': {},
                'metadata': {}
            }
    
    def get_cost_estimate(self, num_urls: int) -> Dict[str, float]:
        """Estima custos para diferentes métodos"""
        return {
            'firecrawl_estimate': num_urls * 0.001,  # $0.001 por URL
            'traditional_cost': 0.0,  # Grátis (apenas recursos computacionais)
            'hybrid_recommendation': 'Use FireCrawl para URLs problemáticas, tradicional para o resto'
        }


def setup_firecrawl_integration(api_key: str = None) -> Optional[HybridScraper]:
    """Configura integração com FireCrawl"""
    
    if not FIRECRAWL_AVAILABLE:
        logging.error("FireCrawl não está instalado. Use: pip install firecrawl-py")
        return None
    
    # Configurar API key
    if not api_key:
        api_key = os.getenv('FIRECRAWL_API_KEY')
    
    if not api_key:
        logging.warning("API key do FireCrawl não fornecida. Apenas método tradicional disponível.")
        return HybridScraper(use_firecrawl_first=False)
    
    # Criar configuração
    config = FireCrawlConfig(
        api_key=api_key,
        max_requests_per_minute=50,  # Conservador
        timeout=30000
    )
    
    # Criar scraper híbrido
    return HybridScraper(config, use_firecrawl_first=True)


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Configurar FireCrawl (substitua pela sua API key)
    api_key = os.getenv('FIRECRAWL_API_KEY', 'sua-api-key-aqui')
    
    if api_key and api_key != 'sua-api-key-aqui':
        # Teste com FireCrawl
        scraper = setup_firecrawl_integration(api_key)
        
        if scraper:
            # URLs de teste
            test_urls = [
                "https://www.godofprompt.ai/prompt/marketing-example"
            ]
            
            # Testar scraping
            for url in test_urls:
                result = scraper.scrape_url(url)
                
                if result['success']:
                    print(f"✅ Sucesso: {url}")
                    print(f"Título: {result['content']['title']}")
                    print(f"Método: {result['metadata']['scraping_method']}")
                else:
                    print(f"❌ Falha: {url} - {result.get('error')}")
            
            # Mostrar estatísticas de custo
            if scraper.firecrawl_scraper:
                stats = scraper.firecrawl_scraper.get_usage_stats()
                print(f"Custo total estimado: ${stats['total_cost']:.3f}")
        else:
            print("Falha ao inicializar scraper")
    else:
        print("Configure FIRECRAWL_API_KEY para testar a integração")