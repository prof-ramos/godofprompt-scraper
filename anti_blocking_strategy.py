#!/usr/bin/env python3
"""
Estratégias avançadas para evitar bloqueios e otimizar performance no GodOfPrompt scraper
"""

import random
import time
import json
import hashlib
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from urllib.parse import urljoin
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests


@dataclass
class ScrapingConfig:
    """Configurações avançadas para scraping defensivo"""
    
    # Anti-detecção
    user_agents: List[str] = field(default_factory=lambda: [
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
    ])
    
    # Delays adaptativos
    min_delay: float = 2.0
    max_delay: float = 8.0
    page_load_delay: float = 3.0
    error_backoff_base: float = 5.0
    
    # Performance
    max_retries: int = 3
    request_timeout: int = 30
    max_pages_per_category: int = 50
    concurrent_categories: int = 1  # Conservador por padrão
    
    # Monitoramento
    success_threshold: float = 0.8  # 80% de sucesso mínimo
    block_detection_keywords: List[str] = field(default_factory=lambda: [
        "blocked", "captcha", "rate limit", "too many requests", 
        "access denied", "forbidden", "bot detection"
    ])


class AdaptiveDelayManager:
    """Gerenciador de delays adaptativos baseado em sucesso/falha"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.success_count = 0
        self.error_count = 0
        self.consecutive_errors = 0
        self.current_delay = config.min_delay
        
    def get_delay(self) -> float:
        """Calcula delay adaptativo baseado no histórico"""
        # Aumenta delay após erros consecutivos
        if self.consecutive_errors > 0:
            multiplier = min(2 ** self.consecutive_errors, 8)
            adaptive_delay = self.config.error_backoff_base * multiplier
        else:
            # Diminui gradualmente o delay após sucessos
            success_ratio = self.success_count / max(self.success_count + self.error_count, 1)
            if success_ratio > 0.9:
                adaptive_delay = self.config.min_delay
            else:
                adaptive_delay = self.current_delay
        
        # Adiciona jitter aleatório para mascarar padrões
        jitter = random.uniform(0.5, 1.5)
        final_delay = max(adaptive_delay * jitter, self.config.min_delay)
        final_delay = min(final_delay, self.config.max_delay)
        
        self.current_delay = final_delay
        return final_delay
    
    def record_success(self):
        """Registra uma operação bem-sucedida"""
        self.success_count += 1
        self.consecutive_errors = 0
        
    def record_error(self):
        """Registra uma operação com erro"""
        self.error_count += 1
        self.consecutive_errors += 1


class AntiDetectionDriver:
    """Driver com recursos avançados de anti-detecção"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.delay_manager = AdaptiveDelayManager(config)
        self.session_fingerprint = self._generate_session_id()
        
    def _generate_session_id(self) -> str:
        """Gera ID único para a sessão"""
        timestamp = str(time.time())
        return hashlib.md5(timestamp.encode()).hexdigest()[:8]
        
    def create_driver(self) -> webdriver.Chrome:
        """Cria driver com configurações anti-detecção avançadas"""
        chrome_options = Options()
        
        # Configurações básicas
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        
        # Janela com dimensões variáveis (mais natural)
        width = random.randint(1366, 1920)
        height = random.randint(768, 1080)
        chrome_options.add_argument(f"--window-size={width},{height}")
        
        # User-Agent rotativo
        user_agent = random.choice(self.config.user_agents)
        chrome_options.add_argument(f"--user-agent={user_agent}")
        
        # Anti-detecção avançada
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-plugins")
        chrome_options.add_argument("--disable-images")  # Economiza banda
        chrome_options.add_argument("--disable-javascript-harmony-shipping")
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-backgrounding-occluded-windows")
        chrome_options.add_argument("--disable-renderer-backgrounding")
        
        # Configurações experimentais
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Preferências avançadas
        prefs = {
            "profile.default_content_setting_values": {
                "notifications": 2,
                "media_stream": 2,
            },
            "profile.managed_default_content_settings": {
                "images": 2  # Bloquear imagens para performance
            }
        }
        chrome_options.add_experimental_option("prefs", prefs)
        
        driver = webdriver.Chrome(options=chrome_options)
        
        # Configurações pós-criação
        driver.set_page_load_timeout(self.config.request_timeout)
        driver.implicitly_wait(10)
        
        # Executar script para mascarar automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        logging.info(f"Driver criado - Sessão: {self.session_fingerprint} | UA: {user_agent[:50]}...")
        
        return driver
    
    def smart_wait(self, driver: webdriver.Chrome, condition: Callable, timeout: int = None) -> bool:
        """Espera inteligente com retry e delay adaptativo"""
        if timeout is None:
            timeout = self.config.request_timeout
            
        try:
            WebDriverWait(driver, timeout).until(condition)
            
            # Delay após carregamento bem-sucedido
            delay = self.delay_manager.get_delay()
            logging.debug(f"Aguardando {delay:.2f}s após carregamento...")
            time.sleep(delay)
            
            self.delay_manager.record_success()
            return True
            
        except Exception as e:
            self.delay_manager.record_error()
            logging.warning(f"Timeout na espera: {e}")
            
            # Delay maior após erro
            error_delay = self.delay_manager.get_delay() * 2
            time.sleep(error_delay)
            return False
    
    def safe_get_page(self, driver: webdriver.Chrome, url: str) -> bool:
        """Carregamento seguro de página com detecção de bloqueio"""
        try:
            logging.info(f"Carregando: {url}")
            driver.get(url)
            
            # Verificar se foi bloqueado
            page_content = driver.page_source.lower()
            for keyword in self.config.block_detection_keywords:
                if keyword in page_content:
                    logging.warning(f"Possível bloqueio detectado: '{keyword}' encontrado")
                    self.delay_manager.record_error()
                    return False
            
            self.delay_manager.record_success()
            return True
            
        except Exception as e:
            logging.error(f"Erro carregando página {url}: {e}")
            self.delay_manager.record_error()
            return False


class PerformanceOptimizer:
    """Otimizador de performance para extração em massa"""
    
    def __init__(self, config: ScrapingConfig):
        self.config = config
        self.stats = {
            'pages_processed': 0,
            'prompts_extracted': 0,
            'errors': 0,
            'start_time': time.time(),
            'category_times': {}
        }
    
    def estimate_time_remaining(self, categories_remaining: int) -> str:
        """Estima tempo restante baseado na performance atual"""
        if self.stats['pages_processed'] == 0:
            return "Calculando..."
        
        elapsed = time.time() - self.stats['start_time']
        avg_time_per_page = elapsed / self.stats['pages_processed']
        
        # Estimativa conservadora (assume 10 páginas por categoria)
        estimated_pages = categories_remaining * 10
        estimated_seconds = estimated_pages * avg_time_per_page
        
        if estimated_seconds < 60:
            return f"{estimated_seconds:.0f}s"
        elif estimated_seconds < 3600:
            return f"{estimated_seconds/60:.1f}min"
        else:
            return f"{estimated_seconds/3600:.1f}h"
    
    def get_performance_report(self) -> Dict:
        """Gera relatório de performance detalhado"""
        elapsed = time.time() - self.stats['start_time']
        
        return {
            'tempo_total': f"{elapsed:.1f}s",
            'páginas_processadas': self.stats['pages_processed'],
            'prompts_extraídos': self.stats['prompts_extracted'],
            'taxa_de_erro': f"{(self.stats['errors'] / max(self.stats['pages_processed'], 1)) * 100:.1f}%",
            'prompts_por_segundo': f"{self.stats['prompts_extracted'] / max(elapsed, 1):.2f}",
            'páginas_por_minuto': f"{self.stats['pages_processed'] / max(elapsed/60, 1):.1f}",
            'tempos_por_categoria': self.stats['category_times']
        }
    
    def should_continue_category(self, category_name: str, current_page: int, 
                                success_rate: float) -> bool:
        """Decide se deve continuar processando uma categoria"""
        # Parar se taxa de sucesso muito baixa
        if success_rate < self.config.success_threshold and current_page > 3:
            logging.warning(f"Taxa de sucesso baixa para {category_name}: {success_rate:.2f}")
            return False
        
        # Respeitar limite máximo de páginas
        if current_page >= self.config.max_pages_per_category:
            logging.info(f"Limite de páginas atingido para {category_name}")
            return False
        
        return True


class CircuitBreaker:
    """Circuit Breaker para proteger contra falhas em cascata"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 300):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = 'CLOSED'  # CLOSED, OPEN, HALF_OPEN
    
    def call(self, func, *args, **kwargs):
        """Executa função com proteção do circuit breaker"""
        if self.state == 'OPEN':
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = 'HALF_OPEN'
                logging.info("Circuit breaker mudou para HALF_OPEN")
            else:
                raise Exception("Circuit breaker está OPEN - muitas falhas")
        
        try:
            result = func(*args, **kwargs)
            
            # Resetar contador em caso de sucesso
            if self.state == 'HALF_OPEN':
                self.state = 'CLOSED'
                self.failure_count = 0
                logging.info("Circuit breaker voltou para CLOSED")
            
            return result
            
        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = time.time()
            
            if self.failure_count >= self.failure_threshold:
                self.state = 'OPEN'
                logging.error(f"Circuit breaker ABERTO após {self.failure_count} falhas")
            
            raise e


def create_enhanced_scraper(config: ScrapingConfig = None):
    """Factory para criar scraper com todas as otimizações"""
    if config is None:
        config = ScrapingConfig()
    
    return {
        'driver_manager': AntiDetectionDriver(config),
        'performance': PerformanceOptimizer(config),
        'circuit_breaker': CircuitBreaker(),
        'config': config
    }


# Exemplo de uso integrado
if __name__ == "__main__":
    # Configuração personalizada
    config = ScrapingConfig(
        min_delay=3.0,
        max_delay=10.0,
        max_pages_per_category=30,
        concurrent_categories=1
    )
    
    # Criar componentes
    components = create_enhanced_scraper(config)
    driver_manager = components['driver_manager']
    perf = components['performance']
    
    # Exemplo de uso
    driver = driver_manager.create_driver()
    
    try:
        # Simular carregamento de página
        success = driver_manager.safe_get_page(driver, "https://www.godofprompt.ai")
        
        if success:
            print("Página carregada com sucesso!")
            print("Relatório de performance:", perf.get_performance_report())
        else:
            print("Falha no carregamento")
    
    finally:
        driver.quit()