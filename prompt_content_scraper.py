#!/usr/bin/env python3
"""
Scraper de conteúdo individual de prompts do GodOfPrompt.ai
Extrai o conteúdo completo de cada prompt após obter os links
"""

import time
import json
import logging
import asyncio
import aiohttp
import concurrent.futures
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from urllib.parse import urljoin, urlparse
import re
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Importar sistemas desenvolvidos
from login_automation import LoginAutomator, LoginCredentials, SessionConfig
from anti_blocking_strategy import AntiDetectionDriver, ScrapingConfig
from monitoring_system import SystemMonitor


@dataclass
class PromptData:
    """Estrutura de dados completa de um prompt"""
    
    # Metadados básicos
    id: str
    title: str
    url: str
    category: str
    
    # Conteúdo principal
    prompt_text: str = ""
    description: str = ""
    instructions: str = ""
    
    # Metadados adicionais
    tags: List[str] = field(default_factory=list)
    difficulty: str = ""
    estimated_tokens: int = 0
    use_cases: List[str] = field(default_factory=list)
    
    # Informações de extração
    extracted_at: str = ""
    extraction_method: str = ""
    success: bool = False
    error_message: str = ""
    
    # Dados brutos para debugging
    raw_html: str = ""
    
    def to_dict(self) -> Dict:
        """Converte para dicionário"""
        return {
            'id': self.id,
            'title': self.title,
            'url': self.url,
            'category': self.category,
            'content': {
                'prompt_text': self.prompt_text,
                'description': self.description,
                'instructions': self.instructions
            },
            'metadata': {
                'tags': self.tags,
                'difficulty': self.difficulty,
                'estimated_tokens': self.estimated_tokens,
                'use_cases': self.use_cases
            },
            'extraction_info': {
                'extracted_at': self.extracted_at,
                'extraction_method': self.extraction_method,
                'success': self.success,
                'error_message': self.error_message
            }
        }


class PromptContentExtractor:
    """Extrator de conteúdo individual de prompts"""
    
    def __init__(self, login_system: LoginAutomator = None, 
                 monitor: SystemMonitor = None):
        self.login_system = login_system
        self.monitor = monitor
        self.session = None
        
        # Configurações de extração
        self.extraction_config = {
            'timeout': 30,
            'max_retries': 3,
            'retry_delay': 5,
            'use_selenium_fallback': True,
            'content_selectors': {
                # Seletores CSS para diferentes elementos (podem mudar)
                'prompt_text': [
                    'div[class*="prompt-text"]',
                    'div[class*="content"]',
                    'pre',
                    'code',
                    '.prompt-content',
                    '[data-prompt-text]'
                ],
                'title': [
                    'h1',
                    'h2',
                    '.prompt-title',
                    '[data-prompt-title]'
                ],
                'description': [
                    '.description',
                    '.prompt-description', 
                    'p[class*="desc"]',
                    '[data-description]'
                ],
                'tags': [
                    '.tag',
                    '.badge',
                    '.chip',
                    '[data-tags] span'
                ]
            }
        }
        
        # Padrões para limpeza de texto
        self.text_patterns = {
            'clean_whitespace': re.compile(r'\s+'),
            'remove_artifacts': re.compile(r'[\u200b-\u200d\ufeff]'),
            'extract_tokens': re.compile(r'(\d+)\s*tokens?', re.IGNORECASE)
        }
    
    def setup_session(self):
        """Configura sessão autenticada"""
        if self.login_system:
            self.session = self.login_system.get_authenticated_session()
        else:
            self.session = requests.Session()
            # Headers básicos para parecer navegador real
            self.session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1'
            })
    
    def extract_single_prompt(self, prompt_url: str, prompt_id: str = None, 
                            category: str = "unknown") -> PromptData:
        """Extrai conteúdo de um único prompt"""
        
        if not prompt_id:
            prompt_id = self._extract_id_from_url(prompt_url)
        
        prompt_data = PromptData(
            id=prompt_id,
            title="",
            url=prompt_url,
            category=category,
            extracted_at=time.strftime("%Y-%m-%d %H:%M:%S")
        )
        
        # Registrar tentativa no monitor
        if self.monitor:
            start_time = time.time()
        
        try:
            # Método 1: Requests com sessão autenticada
            success = self._extract_with_requests(prompt_data)
            
            if not success and self.extraction_config['use_selenium_fallback']:
                # Método 2: Fallback com Selenium
                logging.info(f"Fallback para Selenium: {prompt_url}")
                success = self._extract_with_selenium(prompt_data)
            
            if success:
                prompt_data.success = True
                logging.info(f"✅ Prompt extraído: {prompt_id}")
            else:
                prompt_data.error_message = "Falha em todos os métodos de extração"
                logging.warning(f"❌ Falha na extração: {prompt_id}")
            
        except Exception as e:
            prompt_data.error_message = str(e)
            logging.error(f"Erro extraindo {prompt_id}: {e}")
        
        # Registrar resultado no monitor
        if self.monitor:
            response_time = time.time() - start_time
            self.monitor.record_request(prompt_data.success, response_time, 
                                      prompt_data.error_message if not prompt_data.success else None)
        
        return prompt_data
    
    def _extract_with_requests(self, prompt_data: PromptData) -> bool:
        """Extração usando requests (mais rápido)"""
        try:
            if not self.session:
                self.setup_session()
            
            response = self.session.get(
                prompt_data.url, 
                timeout=self.extraction_config['timeout']
            )
            
            if response.status_code == 200:
                # Verificar se foi redirecionado para login (paywall)
                if 'signin' in response.url or 'login' in response.url:
                    logging.warning(f"Redirecionado para login: {prompt_data.url}")
                    return False
                
                prompt_data.raw_html = response.text
                prompt_data.extraction_method = "requests"
                
                # Parsear conteúdo
                return self._parse_html_content(prompt_data, response.text)
            else:
                logging.warning(f"Status code {response.status_code} para {prompt_data.url}")
                return False
                
        except Exception as e:
            logging.error(f"Erro em requests para {prompt_data.url}: {e}")
            return False
    
    def _extract_with_selenium(self, prompt_data: PromptData) -> bool:
        """Extração usando Selenium (fallback mais robusto)"""
        driver = None
        
        try:
            # Usar driver anti-detecção se disponível
            config = ScrapingConfig()
            anti_detection = AntiDetectionDriver(config)
            driver = anti_detection.create_driver()
            
            # Carregar página
            driver.get(prompt_data.url)
            
            # Aguardar carregamento do conteúdo
            WebDriverWait(driver, 15).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Aguardar conteúdo específico (se possível)
            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.TAG_NAME, "main"))
                )
            except:
                pass  # Continuar mesmo se não encontrar
            
            time.sleep(3)  # Aguardar JavaScript
            
            prompt_data.raw_html = driver.page_source
            prompt_data.extraction_method = "selenium"
            
            # Parsear conteúdo
            return self._parse_html_content(prompt_data, driver.page_source)
            
        except Exception as e:
            logging.error(f"Erro em Selenium para {prompt_data.url}: {e}")
            return False
        
        finally:
            if driver:
                driver.quit()
    
    def _parse_html_content(self, prompt_data: PromptData, html_content: str) -> bool:
        """Parseia conteúdo HTML e extrai informações"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Extrair título
            prompt_data.title = self._extract_by_selectors(
                soup, self.extraction_config['content_selectors']['title']
            )
            
            # Extrair texto principal do prompt
            prompt_data.prompt_text = self._extract_by_selectors(
                soup, self.extraction_config['content_selectors']['prompt_text']
            )
            
            # Extrair descrição
            prompt_data.description = self._extract_by_selectors(
                soup, self.extraction_config['content_selectors']['description']
            )
            
            # Extrair tags
            tags = self._extract_multiple_by_selectors(
                soup, self.extraction_config['content_selectors']['tags']
            )
            prompt_data.tags = [self._clean_text(tag) for tag in tags if tag.strip()]
            
            # Tentar estimar número de tokens
            full_text = f"{prompt_data.title} {prompt_data.prompt_text} {prompt_data.description}"
            prompt_data.estimated_tokens = self._estimate_tokens(full_text)
            
            # Extrair informações adicionais via padrões
            self._extract_additional_metadata(prompt_data, soup)
            
            # Validar se conseguiu extrair conteúdo mínimo
            if prompt_data.title or prompt_data.prompt_text:
                return True
            else:
                logging.warning(f"Nenhum conteúdo principal extraído de {prompt_data.url}")
                return False
                
        except Exception as e:
            logging.error(f"Erro parseando HTML: {e}")
            return False
    
    def _extract_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> str:
        """Extrai texto usando lista de seletores CSS"""
        for selector in selectors:
            try:
                element = soup.select_one(selector)
                if element:
                    text = element.get_text(strip=True)
                    if text:
                        return self._clean_text(text)
            except Exception as e:
                logging.debug(f"Erro no seletor {selector}: {e}")
                continue
        return ""
    
    def _extract_multiple_by_selectors(self, soup: BeautifulSoup, selectors: List[str]) -> List[str]:
        """Extrai múltiplos textos usando lista de seletores CSS"""
        results = []
        for selector in selectors:
            try:
                elements = soup.select(selector)
                for element in elements:
                    text = element.get_text(strip=True)
                    if text and text not in results:
                        results.append(text)
            except Exception as e:
                logging.debug(f"Erro no seletor múltiplo {selector}: {e}")
                continue
        return results
    
    def _extract_additional_metadata(self, prompt_data: PromptData, soup: BeautifulSoup):
        """Extrai metadados adicionais do HTML"""
        try:
            # Procurar por indicadores de dificuldade
            full_text = soup.get_text().lower()
            
            difficulty_patterns = {
                'beginner': r'\b(beginner|iniciante|básico|easy|fácil)\b',
                'intermediate': r'\b(intermediate|intermediário|médio|medium)\b',
                'advanced': r'\b(advanced|avançado|expert|difícil|hard)\b'
            }
            
            for level, pattern in difficulty_patterns.items():
                if re.search(pattern, full_text):
                    prompt_data.difficulty = level
                    break
            
            # Extrair casos de uso de seções específicas
            use_case_keywords = ['use case', 'caso de uso', 'aplicação', 'exemplo']
            for keyword in use_case_keywords:
                pattern = rf'{keyword}[^.]*\.([^.]*\.)'
                matches = re.findall(pattern, full_text, re.IGNORECASE)
                if matches:
                    prompt_data.use_cases.extend([match.strip() for match in matches[:3]])
            
        except Exception as e:
            logging.debug(f"Erro extraindo metadados adicionais: {e}")
    
    def _clean_text(self, text: str) -> str:
        """Limpa e normaliza texto extraído"""
        if not text:
            return ""
        
        # Remover caracteres invisíveis
        text = self.text_patterns['remove_artifacts'].sub('', text)
        
        # Normalizar espaços
        text = self.text_patterns['clean_whitespace'].sub(' ', text)
        
        return text.strip()
    
    def _estimate_tokens(self, text: str) -> int:
        """Estima número de tokens no texto"""
        if not text:
            return 0
        
        # Método simples: ~4 caracteres por token (aproximação)
        return len(text) // 4
    
    def _extract_id_from_url(self, url: str) -> str:
        """Extrai ID do prompt da URL"""
        try:
            # Padrões comuns de URL
            patterns = [
                r'/prompt/([^/?]+)',
                r'prompt=([^&]+)',
                r'/([^/?]+)/?$'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # Fallback: usar hash da URL
            return str(hash(url))[-8:]
            
        except Exception:
            return str(hash(url))[-8:]
    
    def extract_multiple_prompts(self, prompt_urls: List[Dict], 
                                max_workers: int = 5) -> List[PromptData]:
        """Extrai múltiplos prompts em paralelo"""
        
        logging.info(f"Iniciando extração de {len(prompt_urls)} prompts")
        
        results = []
        
        # Processar em lotes para controlar recursos
        batch_size = max_workers * 2
        for i in range(0, len(prompt_urls), batch_size):
            batch = prompt_urls[i:i + batch_size]
            logging.info(f"Processando lote {i//batch_size + 1}: {len(batch)} prompts")
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                # Submeter tarefas
                future_to_url = {
                    executor.submit(
                        self.extract_single_prompt, 
                        prompt['url'], 
                        prompt.get('id'), 
                        prompt.get('category', 'unknown')
                    ): prompt for prompt in batch
                }
                
                # Coletar resultados
                for future in concurrent.futures.as_completed(future_to_url, timeout=300):
                    try:
                        result = future.result()
                        results.append(result)
                    except Exception as e:
                        prompt = future_to_url[future]
                        logging.error(f"Erro processando {prompt['url']}: {e}")
                        # Criar registro de erro
                        error_data = PromptData(
                            id=prompt.get('id', 'unknown'),
                            title="",
                            url=prompt['url'],
                            category=prompt.get('category', 'unknown'),
                            error_message=str(e),
                            extracted_at=time.strftime("%Y-%m-%d %H:%M:%S")
                        )
                        results.append(error_data)
            
            # Pausa entre lotes
            if i + batch_size < len(prompt_urls):
                time.sleep(5)
        
        logging.info(f"Extração completa: {len(results)} prompts processados")
        
        # Estatísticas
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful
        logging.info(f"Sucessos: {successful}, Falhas: {failed}")
        
        return results


def save_prompt_data(prompts: List[PromptData], output_file: str = None):
    """Salva dados de prompts em arquivo JSON"""
    if not output_file:
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        output_file = f"prompt_content_{timestamp}.json"
    
    # Converter para formato serializável
    data = {
        'extraction_info': {
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_prompts': len(prompts),
            'successful_extractions': sum(1 for p in prompts if p.success),
            'failed_extractions': sum(1 for p in prompts if not p.success)
        },
        'prompts': [prompt.to_dict() for prompt in prompts]
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Dados salvos em: {output_file}")
    return output_file


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # URLs de exemplo
    test_urls = [
        {
            'url': 'https://www.godofprompt.ai/prompt/marketing-example',
            'id': 'marketing-001',
            'category': 'Marketing'
        }
    ]
    
    # Criar extrator
    extractor = PromptContentExtractor()
    
    # Extrair prompts
    results = extractor.extract_multiple_prompts(test_urls, max_workers=3)
    
    # Salvar resultados
    output_file = save_prompt_data(results)
    print(f"Dados salvos em: {output_file}")
    
    # Mostrar estatísticas
    successful = sum(1 for r in results if r.success)
    print(f"Prompts extraídos com sucesso: {successful}/{len(results)}")