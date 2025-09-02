#!/usr/bin/env python3
"""
Sistema de automação de login para bypass de paywall no GodOfPrompt.ai
"""

import time
import json
import logging
import os
from typing import Dict, Optional, List, Tuple
from dataclasses import dataclass
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import requests
from urllib.parse import urljoin, urlparse


@dataclass
class LoginCredentials:
    """Credenciais de login"""
    email: str
    password: str
    backup_email: Optional[str] = None
    backup_password: Optional[str] = None


@dataclass
class SessionConfig:
    """Configuração de sessão"""
    session_timeout: int = 3600  # 1 hora
    max_login_attempts: int = 3
    cookie_file: str = "session_cookies.json"
    headers_file: str = "session_headers.json"
    
    # Seletores do site (podem mudar)
    login_url: str = "https://www.godofprompt.ai/auth/signin"
    email_selector: str = 'input[type="email"]'
    password_selector: str = 'input[type="password"]'
    login_button_selector: str = 'button[type="submit"]'
    
    # Indicadores de login bem-sucedido
    success_indicators: List[str] = None
    
    def __post_init__(self):
        if self.success_indicators is None:
            self.success_indicators = [
                '/dashboard',
                'premium',
                'logout',
                'profile'
            ]


class SessionManager:
    """Gerenciador de sessão com persistência"""
    
    def __init__(self, config: SessionConfig):
        self.config = config
        self.session_cookies = {}
        self.session_headers = {}
        self.session_valid_until = 0
        self.load_session()
    
    def save_session(self, cookies: Dict, headers: Dict):
        """Salva sessão no disco"""
        try:
            # Salvar cookies
            with open(self.config.cookie_file, 'w') as f:
                json.dump(cookies, f)
            
            # Salvar headers
            with open(self.config.headers_file, 'w') as f:
                json.dump(headers, f)
            
            # Definir validade
            self.session_valid_until = time.time() + self.config.session_timeout
            
            logging.info("Sessão salva com sucesso")
            
        except Exception as e:
            logging.error(f"Erro salvando sessão: {e}")
    
    def load_session(self) -> bool:
        """Carrega sessão do disco"""
        try:
            # Carregar cookies
            if os.path.exists(self.config.cookie_file):
                with open(self.config.cookie_file, 'r') as f:
                    self.session_cookies = json.load(f)
            
            # Carregar headers
            if os.path.exists(self.config.headers_file):
                with open(self.config.headers_file, 'r') as f:
                    self.session_headers = json.load(f)
            
            # Verificar se ainda é válida
            if time.time() < self.session_valid_until and self.session_cookies:
                logging.info("Sessão válida carregada do disco")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Erro carregando sessão: {e}")
            return False
    
    def is_session_valid(self) -> bool:
        """Verifica se sessão ainda é válida"""
        return (time.time() < self.session_valid_until and 
                bool(self.session_cookies))
    
    def clear_session(self):
        """Limpa sessão atual"""
        self.session_cookies = {}
        self.session_headers = {}
        self.session_valid_until = 0
        
        # Remover arquivos
        for file in [self.config.cookie_file, self.config.headers_file]:
            try:
                if os.path.exists(file):
                    os.remove(file)
            except Exception as e:
                logging.warning(f"Erro removendo {file}: {e}")


class LoginAutomator:
    """Automatizador de login com recursos avançados"""
    
    def __init__(self, credentials: LoginCredentials, config: SessionConfig = None):
        self.credentials = credentials
        self.config = config or SessionConfig()
        self.session_manager = SessionManager(self.config)
        self.driver = None
    
    def create_driver(self) -> webdriver.Chrome:
        """Cria driver otimizado para login"""
        if self.driver:
            return self.driver
            
        chrome_options = Options()
        
        # Configurações para parecer usuário real
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1366,768")  # Tamanho comum
        
        # User-Agent realista
        chrome_options.add_argument(
            "--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        
        # Anti-detecção
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Manter perfil para cookies
        chrome_options.add_argument("--disable-web-security")
        chrome_options.add_argument("--allow-running-insecure-content")
        
        self.driver = webdriver.Chrome(options=chrome_options)
        self.driver.set_page_load_timeout(30)
        
        # Script anti-detecção
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def perform_login(self, use_headless: bool = False) -> Tuple[bool, Dict]:
        """Executa processo completo de login"""
        
        # Verificar se já temos sessão válida
        if self.session_manager.is_session_valid():
            logging.info("Sessão válida encontrada - pulando login")
            return True, {
                'cookies': self.session_manager.session_cookies,
                'headers': self.session_manager.session_headers
            }
        
        logging.info("Iniciando processo de login automatizado")
        
        # Tentar login
        for attempt in range(self.config.max_login_attempts):
            try:
                success, session_data = self._attempt_login(attempt + 1, use_headless)
                
                if success:
                    # Salvar sessão
                    self.session_manager.save_session(
                        session_data['cookies'], 
                        session_data['headers']
                    )
                    
                    logging.info("Login realizado com sucesso!")
                    return True, session_data
                else:
                    logging.warning(f"Tentativa {attempt + 1} falhou")
                    time.sleep(5 * (attempt + 1))  # Backoff exponencial
                    
            except Exception as e:
                logging.error(f"Erro na tentativa {attempt + 1}: {e}")
                time.sleep(10)
        
        logging.error("Todas as tentativas de login falharam")
        return False, {}
    
    def _attempt_login(self, attempt_num: int, use_headless: bool) -> Tuple[bool, Dict]:
        """Executa uma tentativa de login"""
        driver = None
        
        try:
            # Modificar opções para tentativa específica
            if use_headless or attempt_num > 1:
                # Usar headless após primeira tentativa
                chrome_options = Options()
                chrome_options.add_argument("--headless")
                chrome_options.add_argument("--no-sandbox")
                chrome_options.add_argument("--disable-dev-shm-usage")
                
                if self.driver:
                    self.driver.quit()
                self.driver = webdriver.Chrome(options=chrome_options)
            else:
                driver = self.create_driver()
            
            # Navegar para página de login
            logging.info(f"Tentativa {attempt_num}: Navegando para {self.config.login_url}")
            driver.get(self.config.login_url)
            
            # Aguardar carregamento
            time.sleep(3)
            
            # Encontrar e preencher campos
            email_field = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, self.config.email_selector))
            )
            
            password_field = driver.find_element(By.CSS_SELECTOR, self.config.password_selector)
            
            # Simular digitação humana
            self._human_like_typing(email_field, self.credentials.email)
            time.sleep(1)
            self._human_like_typing(password_field, self.credentials.password)
            time.sleep(1)
            
            # Clicar no botão de login
            login_button = driver.find_element(By.CSS_SELECTOR, self.config.login_button_selector)
            
            # Scroll para o botão se necessário
            driver.execute_script("arguments[0].scrollIntoView();", login_button)
            time.sleep(1)
            
            login_button.click()
            
            # Aguardar redirecionamento
            success = self._wait_for_login_success(driver)
            
            if success:
                # Coletar cookies e headers
                cookies = {cookie['name']: cookie['value'] for cookie in driver.get_cookies()}
                
                headers = {
                    'User-Agent': driver.execute_script("return navigator.userAgent;"),
                    'Referer': driver.current_url
                }
                
                return True, {'cookies': cookies, 'headers': headers}
            else:
                # Capturar screenshot para debug se não for headless
                if not use_headless:
                    try:
                        driver.save_screenshot(f"login_fail_{attempt_num}.png")
                        logging.info(f"Screenshot salva: login_fail_{attempt_num}.png")
                    except:
                        pass
                        
                return False, {}
        
        except TimeoutException:
            logging.error(f"Timeout na tentativa {attempt_num}")
            return False, {}
        except NoSuchElementException as e:
            logging.error(f"Elemento não encontrado na tentativa {attempt_num}: {e}")
            return False, {}
        except Exception as e:
            logging.error(f"Erro inesperado na tentativa {attempt_num}: {e}")
            return False, {}
        
        finally:
            if driver and attempt_num == self.config.max_login_attempts:
                driver.quit()
                self.driver = None
    
    def _human_like_typing(self, element, text: str):
        """Simula digitação humana"""
        element.clear()
        for char in text:
            element.send_keys(char)
            time.sleep(0.05 + (0.1 * __import__('random').random()))  # Delay variável
    
    def _wait_for_login_success(self, driver, timeout: int = 15) -> bool:
        """Aguarda indicadores de login bem-sucedido"""
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            try:
                current_url = driver.current_url
                page_source = driver.page_source.lower()
                
                # Verificar indicadores na URL
                for indicator in self.config.success_indicators:
                    if indicator.lower() in current_url.lower():
                        logging.info(f"Login detectado via URL: {indicator}")
                        return True
                
                # Verificar indicadores no conteúdo
                success_keywords = ['dashboard', 'premium content', 'logout', 'profile']
                for keyword in success_keywords:
                    if keyword in page_source:
                        logging.info(f"Login detectado via conteúdo: {keyword}")
                        return True
                
                # Verificar se não está mais na página de login
                if 'signin' not in current_url and 'login' not in current_url:
                    time.sleep(2)  # Aguardar estabilizar
                    if 'signin' not in driver.current_url and 'login' not in driver.current_url:
                        logging.info("Login detectado - redirecionamento da página de login")
                        return True
                
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Erro verificando login: {e}")
                time.sleep(1)
        
        logging.warning("Timeout aguardando confirmação de login")
        return False
    
    def get_authenticated_session(self) -> Optional[requests.Session]:
        """Retorna sessão requests autenticada"""
        if not self.session_manager.is_session_valid():
            logging.warning("Sessão inválida - execute perform_login() primeiro")
            return None
        
        session = requests.Session()
        
        # Adicionar cookies
        for name, value in self.session_manager.session_cookies.items():
            session.cookies.set(name, value)
        
        # Adicionar headers
        session.headers.update(self.session_manager.session_headers)
        
        return session
    
    def test_session_validity(self, test_url: str = None) -> bool:
        """Testa se a sessão ainda está válida"""
        if not test_url:
            test_url = "https://www.godofprompt.ai/dashboard"  # URL que requer login
        
        session = self.get_authenticated_session()
        if not session:
            return False
        
        try:
            response = session.get(test_url, timeout=10)
            
            # Verificar se não foi redirecionado para login
            if 'signin' in response.url or 'login' in response.url:
                logging.info("Sessão expirada - redirecionado para login")
                self.session_manager.clear_session()
                return False
            
            if response.status_code == 200:
                logging.info("Sessão ainda válida")
                return True
            else:
                logging.warning(f"Resposta inesperada: {response.status_code}")
                return False
                
        except Exception as e:
            logging.error(f"Erro testando sessão: {e}")
            return False
    
    def cleanup(self):
        """Limpa recursos"""
        if self.driver:
            self.driver.quit()
            self.driver = None


def create_login_system(email: str, password: str) -> LoginAutomator:
    """Factory para criar sistema de login"""
    
    credentials = LoginCredentials(
        email=email,
        password=password
    )
    
    config = SessionConfig(
        session_timeout=7200,  # 2 horas
        max_login_attempts=3,
        login_url="https://www.godofprompt.ai/auth/signin"
    )
    
    return LoginAutomator(credentials, config)


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Criar sistema (substitua pelas credenciais reais)
    login_system = create_login_system(
        email="seu_email@exemplo.com",
        password="sua_senha"
    )
    
    try:
        # Realizar login
        success, session_data = login_system.perform_login()
        
        if success:
            print("Login realizado com sucesso!")
            
            # Testar sessão
            if login_system.test_session_validity():
                print("Sessão válida e pronta para uso")
                
                # Obter sessão para requests
                session = login_system.get_authenticated_session()
                if session:
                    print("Sessão requests configurada")
            else:
                print("Problema com validação da sessão")
        else:
            print("Falha no login")
    
    finally:
        login_system.cleanup()