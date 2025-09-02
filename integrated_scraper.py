#!/usr/bin/env python3
"""
Scraper integrado com sistema de armazenamento inteligente
Combina extração de links/conteúdo com organização automática de arquivos
"""

import os
import sys
import time
import logging
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

# Importar todos os módulos desenvolvidos
from extract_links import load_categories, extract_category_links, create_driver
from login_automation import create_login_system
from prompt_content_scraper import PromptContentExtractor, PromptData
from storage_manager import create_storage_system, StorageConfig
from monitoring_system import create_monitoring_system
from performance_optimizer import OptimizedScraper
from anti_blocking_strategy import create_enhanced_scraper


class IntegratedGodOfPromptScraper:
    """Scraper completo e integrado do GodOfPrompt.ai"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = self._setup_config(config or {})
        
        # Componentes do sistema
        self.storage_system = None
        self.login_system = None
        self.content_extractor = None
        self.monitoring_system = None
        self.performance_optimizer = None
        
        # Estado da execução
        self.execution_stats = {
            'start_time': time.time(),
            'phase': 'initialization',
            'categories_processed': 0,
            'links_extracted': 0,
            'prompts_extracted': 0,
            'files_saved': 0
        }
        
        self._setup_logging()
        self._initialize_systems()
    
    def _setup_config(self, user_config: Dict) -> Dict:
        """Configura parâmetros do sistema"""
        default_config = {
            # Comportamento geral
            'extract_content': True,          # Se deve extrair conteúdo dos prompts
            'organize_by_category': True,     # Organizar arquivos por categoria
            'create_backups': True,           # Backup de arquivos existentes
            
            # Credenciais (podem vir de variáveis de ambiente)
            'email': os.getenv('GODOFPROMPT_EMAIL', ''),
            'password': os.getenv('GODOFPROMPT_PASSWORD', ''),
            'firecrawl_api_key': os.getenv('FIRECRAWL_API_KEY', ''),
            
            # Armazenamento
            'storage_format': 'markdown',     # markdown, json, txt
            'base_directory': 'godofprompt_data',
            
            # Performance
            'max_workers': 3,
            'batch_size': 5,
            'delays': {'min': 3, 'max': 8},
            'use_cache': True,
            
            # Limites
            'max_pages_per_category': 30,
            'max_retries': 3,
            'session_timeout': 7200,  # 2 horas
            
            # Modo de execução
            'interactive': True,              # Perguntar confirmações
            'verbose': True,                  # Logs detalhados
            'test_mode': False,               # Apenas algumas categorias para teste
        }
        
        # Combinar configurações
        config = {**default_config, **user_config}
        
        return config
    
    def _setup_logging(self):
        """Configura sistema de logging"""
        log_level = logging.DEBUG if self.config['verbose'] else logging.INFO
        
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(
                    os.path.join(self.config['base_directory'], 'integrated_scraper.log')
                ),
                logging.StreamHandler()
            ]
        )
        
        # Criar diretório de logs se não existe
        Path(self.config['base_directory']).mkdir(exist_ok=True)
    
    def _initialize_systems(self):
        """Inicializa todos os sistemas necessários"""
        logging.info("🔧 Inicializando sistemas integrados...")
        
        # 1. Sistema de armazenamento
        storage_config = StorageConfig(
            base_dir=self.config['base_directory'],
            organize_by_category=self.config['organize_by_category'],
            prompt_format=self.config['storage_format'],
            create_backups=self.config['create_backups']
        )
        
        self.storage_system = create_storage_system(
            organize_by_category=self.config['organize_by_category'],
            prompt_format=self.config['storage_format']
        )
        
        # 2. Sistema de login (se credenciais fornecidas)
        if self.config['email'] and self.config['password']:
            try:
                self.login_system = create_login_system(
                    self.config['email'], 
                    self.config['password']
                )
                logging.info("✅ Sistema de login inicializado")
            except Exception as e:
                logging.warning(f"⚠️  Falha no sistema de login: {e}")
        
        # 3. Sistema de monitoramento
        self.monitoring_system = create_monitoring_system()
        self.monitoring_system['start']()
        
        # 4. Otimizador de performance
        perf_config = {
            'batch_size': self.config['batch_size'],
            'max_workers': self.config['max_workers'],
            'use_cache': self.config['use_cache'],
            'monitor_resources': True
        }
        
        self.performance_optimizer = OptimizedScraper(perf_config)
        
        # 5. Extrator de conteúdo (se necessário)
        if self.config['extract_content']:
            self.content_extractor = PromptContentExtractor(
                login_system=self.login_system,
                monitor=self.monitoring_system['monitor']
            )
        
        logging.info("✅ Todos os sistemas inicializados")
    
    def run_complete_extraction(self) -> Dict[str, Any]:
        """Executa extração completa - links + conteúdo + armazenamento"""
        
        print("🚀 === SCRAPER INTEGRADO GODOFPROMPT.AI ===\n")
        
        try:
            # Fase 1: Carregar categorias e configurar
            categories = self._load_and_configure_categories()
            
            # Fase 2: Extração de links
            links_data = self._extract_all_links(categories)
            
            # Fase 3: Login e extração de conteúdo (se habilitado)
            prompts_data = None
            if self.config['extract_content'] and links_data:
                if self._should_extract_content(links_data):
                    prompts_data = self._extract_all_content(links_data)
            
            # Fase 4: Armazenamento inteligente
            storage_results = self._store_results(links_data, prompts_data)
            
            # Fase 5: Relatório final
            return self._generate_final_report(categories, links_data, prompts_data, storage_results)
            
        except KeyboardInterrupt:
            logging.warning("⚠️  Execução interrompida pelo usuário")
            return {'status': 'interrupted', 'partial_results': True}
        except Exception as e:
            logging.error(f"❌ Erro crítico na execução: {e}")
            return {'status': 'error', 'error': str(e)}
        finally:
            self._cleanup()
    
    def _load_and_configure_categories(self) -> List[Dict]:
        """Carrega e configura categorias para extração"""
        logging.info("📋 Carregando categorias...")
        
        categories = load_categories()
        
        # Modo teste - apenas algumas categorias
        if self.config['test_mode']:
            categories = categories[:2]  # Apenas 2 primeiras
            logging.info(f"🧪 Modo teste: processando apenas {len(categories)} categorias")
        
        # Exibir categorias
        print(f"\n📋 CATEGORIAS A SEREM PROCESSADAS ({len(categories)}):")
        total_esperado = 0
        for i, cat in enumerate(categories, 1):
            print(f"  {i}. {cat['nome']}: {cat['quantidadeDePrompts']} prompts")
            total_esperado += cat['quantidadeDePrompts']
        
        print(f"\n📊 Total esperado: {total_esperado} prompts")
        
        # Confirmação interativa
        if self.config['interactive']:
            continuar = input("\nDeseja continuar? (s/n): ").lower().strip()
            if continuar != 's':
                print("❌ Extração cancelada pelo usuário")
                sys.exit(0)
        
        return categories
    
    def _extract_all_links(self, categories: List[Dict]) -> Dict[str, Any]:
        """Extrai todos os links usando sistema otimizado"""
        self.execution_stats['phase'] = 'link_extraction'
        
        print("\n🔗 === FASE 1: EXTRAÇÃO DE LINKS ===")
        logging.info("Iniciando extração de links...")
        
        # Usar extrator otimizado se disponível
        if self.performance_optimizer:
            def extract_wrapper(category):
                return extract_category_links(category)
            
            results = self.performance_optimizer.extract_all_categories(
                categories, extract_wrapper
            )
        else:
            # Fallback para método tradicional
            results = self._extract_links_traditional(categories)
        
        # Contabilizar resultados
        total_links = sum(len(links) for links in results.values())
        self.execution_stats['links_extracted'] = total_links
        self.execution_stats['categories_processed'] = len(results)
        
        print(f"✅ Extração de links concluída: {total_links} links extraídos")
        
        return results
    
    def _extract_links_traditional(self, categories: List[Dict]) -> Dict[str, List]:
        """Método tradicional de extração de links (fallback)"""
        results = {}
        driver = create_driver()
        
        try:
            for i, category in enumerate(categories, 1):
                print(f"\n🔄 [{i}/{len(categories)}] {category['nome']}")
                
                links = extract_category_links(category, driver, should_close_driver=False)
                results[category['nome']] = links
                
                print(f"✅ {len(links)} links extraídos")
                time.sleep(2)  # Pausa entre categorias
        finally:
            if driver:
                driver.quit()
        
        return results
    
    def _should_extract_content(self, links_data: Dict) -> bool:
        """Decide se deve extrair conteúdo dos prompts"""
        total_links = sum(len(links) for links in links_data.values())
        
        if not self.config['extract_content']:
            return False
        
        if not self.login_system:
            print("⚠️  Sistema de login não configurado - pulando extração de conteúdo")
            return False
        
        # Confirmação para muitos prompts
        if self.config['interactive'] and total_links > 100:
            print(f"\n🤔 Foram encontrados {total_links} prompts")
            print("⚠️  A extração de conteúdo pode demorar muito tempo!")
            
            if not self.config['test_mode']:
                continuar = input("Deseja continuar com extração de conteúdo? (s/n): ").lower().strip()
                if continuar != 's':
                    return False
        
        return True
    
    def _extract_all_content(self, links_data: Dict) -> List[PromptData]:
        """Extrai conteúdo completo de todos os prompts"""
        self.execution_stats['phase'] = 'content_extraction'
        
        print("\n📝 === FASE 2: EXTRAÇÃO DE CONTEÚDO ===")
        logging.info("Iniciando extração de conteúdo...")
        
        # Login automático
        if self.login_system:
            print("🔐 Realizando login...")
            success, session_data = self.login_system.perform_login(use_headless=True)
            
            if not success:
                print("❌ Falha no login - pulando extração de conteúdo")
                return None
            
            print("✅ Login realizado com sucesso")
        
        # Preparar lista de URLs
        all_urls = []
        for category_name, links in links_data.items():
            for link_data in links:
                all_urls.append({
                    'url': link_data['url'],
                    'id': link_data.get('id', 'unknown'),
                    'category': category_name,
                    'name': link_data.get('name', 'Sem título')
                })
        
        # Extrair conteúdo
        if self.content_extractor:
            prompts_data = self.content_extractor.extract_multiple_prompts(
                all_urls, max_workers=self.config['max_workers']
            )
        else:
            print("❌ Extrator de conteúdo não inicializado")
            return None
        
        # Contabilizar
        successful_extractions = sum(1 for p in prompts_data if p.success)
        self.execution_stats['prompts_extracted'] = successful_extractions
        
        print(f"✅ Extração de conteúdo concluída: {successful_extractions}/{len(all_urls)}")
        
        return prompts_data
    
    def _store_results(self, links_data: Dict, prompts_data: List[PromptData] = None) -> Dict[str, Any]:
        """Armazena resultados no sistema de arquivos"""
        self.execution_stats['phase'] = 'storage'
        
        print("\n💾 === FASE 3: ARMAZENAMENTO ===")
        logging.info("Iniciando armazenamento de dados...")
        
        storage_results = {'files_created': [], 'directories_created': []}
        
        # Armazenar prompts completos (se disponíveis)
        if prompts_data:
            print("📄 Salvando prompts completos em arquivos individuais...")
            
            # Converter PromptData para dict
            prompts_dict = [prompt.to_dict() for prompt in prompts_data]
            
            # Salvar usando sistema de armazenamento
            prompt_files = self.storage_system.prompt_storage.save_multiple_prompts(prompts_dict)
            storage_results['files_created'].extend(prompt_files)
            
            print(f"✅ {len(prompt_files)} arquivos de prompt salvos")
        
        # Salvar links (sempre, como fallback/backup)
        if links_data:
            print("🔗 Salvando links em arquivo YAML...")
            
            # Preparar dados para o formato esperado
            formatted_links_data = {}
            for category, links in links_data.items():
                formatted_links_data[category] = links
            
            links_file = self.storage_system.links_storage.save_links_by_category(formatted_links_data)
            storage_results['files_created'].append(links_file)
            
            print(f"✅ Links salvos em: {os.path.basename(links_file)}")
        
        # Salvar metadados da execução
        metadata = self._generate_execution_metadata()
        metadata_file = self._save_execution_metadata(metadata)
        storage_results['files_created'].append(metadata_file)
        
        self.execution_stats['files_saved'] = len(storage_results['files_created'])
        
        return storage_results
    
    def _generate_execution_metadata(self) -> Dict:
        """Gera metadados da execução atual"""
        current_time = time.time()
        
        return {
            'execution_info': {
                'start_time': datetime.fromtimestamp(self.execution_stats['start_time']).isoformat(),
                'end_time': datetime.fromtimestamp(current_time).isoformat(),
                'duration_seconds': current_time - self.execution_stats['start_time'],
                'phase': self.execution_stats['phase']
            },
            'statistics': {
                'categories_processed': self.execution_stats['categories_processed'],
                'links_extracted': self.execution_stats['links_extracted'],
                'prompts_extracted': self.execution_stats['prompts_extracted'],
                'files_saved': self.execution_stats['files_saved']
            },
            'configuration': {
                'extract_content': self.config['extract_content'],
                'storage_format': self.config['storage_format'],
                'organize_by_category': self.config['organize_by_category'],
                'test_mode': self.config['test_mode']
            },
            'system_info': {
                'python_version': sys.version,
                'storage_directory': self.config['base_directory']
            }
        }
    
    def _save_execution_metadata(self, metadata: Dict) -> str:
        """Salva metadados da execução"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"execution_metadata_{timestamp}.json"
        filepath = os.path.join(self.config['base_directory'], 'metadata', filename)
        
        # Garantir que diretório existe
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def _generate_final_report(self, categories: List[Dict], links_data: Dict, 
                              prompts_data: List[PromptData], storage_results: Dict) -> Dict[str, Any]:
        """Gera relatório final da execução"""
        
        print("\n🎉 === RELATÓRIO FINAL ===")
        
        # Estatísticas básicas
        total_expected = sum(cat['quantidadeDePrompts'] for cat in categories)
        total_links = sum(len(links) for links in links_data.values()) if links_data else 0
        total_prompts = len([p for p in prompts_data if p.success]) if prompts_data else 0
        
        duration = time.time() - self.execution_stats['start_time']
        
        # Exibir relatório
        print(f"⏱️  Tempo total: {duration/60:.1f} minutos")
        print(f"📂 Diretório: {self.config['base_directory']}")
        print(f"📊 Categorias processadas: {len(categories)}")
        print(f"🔗 Links extraídos: {total_links}/{total_expected} ({(total_links/max(total_expected,1))*100:.1f}%)")
        
        if prompts_data:
            print(f"📝 Prompts completos: {total_prompts}/{total_links} ({(total_prompts/max(total_links,1))*100:.1f}%)")
        
        print(f"💾 Arquivos criados: {len(storage_results['files_created'])}")
        
        # Estatísticas por categoria
        if links_data:
            print("\n📈 Detalhes por categoria:")
            for category in categories:
                cat_name = category['nome']
                expected = category['quantidadeDePrompts']
                extracted = len(links_data.get(cat_name, []))
                percentage = (extracted / max(expected, 1)) * 100
                print(f"  • {cat_name}: {extracted}/{expected} ({percentage:.1f}%)")
        
        # Performance do sistema
        if self.monitoring_system:
            dashboard = self.monitoring_system['dashboard']()
            print(f"\n⚡ Performance:")
            print(f"  • Taxa de sucesso: {dashboard['performance']['success_rate']:.1%}")
            print(f"  • Tempo médio/requisição: {dashboard['performance']['avg_response_time']:.1f}s")
        
        # Localização dos arquivos
        print(f"\n📁 Arquivos salvos em:")
        print(f"  • Base: {self.config['base_directory']}/")
        
        if prompts_data:
            print(f"  • Prompts: {self.config['base_directory']}/prompts/")
        if links_data:
            print(f"  • Links: {self.config['base_directory']}/links/")
        
        # Estrutura do relatório para retorno
        report = {
            'status': 'completed',
            'duration_minutes': duration / 60,
            'statistics': {
                'total_expected': total_expected,
                'links_extracted': total_links,
                'prompts_extracted': total_prompts,
                'categories_processed': len(categories),
                'files_created': len(storage_results['files_created'])
            },
            'storage': {
                'base_directory': self.config['base_directory'],
                'files_created': storage_results['files_created']
            },
            'performance': self.monitoring_system['dashboard']() if self.monitoring_system else None
        }
        
        return report
    
    def _cleanup(self):
        """Limpa recursos utilizados"""
        logging.info("🧹 Limpando recursos...")
        
        if self.monitoring_system:
            self.monitoring_system['stop']()
        
        if self.login_system:
            self.login_system.cleanup()
        
        logging.info("✅ Limpeza concluída")


# Funções de conveniência para uso fácil
def run_links_only_extraction(test_mode: bool = False) -> Dict[str, Any]:
    """Executa apenas extração de links"""
    config = {
        'extract_content': False,
        'test_mode': test_mode,
        'interactive': True
    }
    
    scraper = IntegratedGodOfPromptScraper(config)
    return scraper.run_complete_extraction()


def run_full_extraction(email: str = None, password: str = None, 
                       test_mode: bool = False) -> Dict[str, Any]:
    """Executa extração completa (links + conteúdo)"""
    config = {
        'extract_content': True,
        'email': email or os.getenv('GODOFPROMPT_EMAIL', ''),
        'password': password or os.getenv('GODOFPROMPT_PASSWORD', ''),
        'test_mode': test_mode,
        'interactive': True,
        'storage_format': 'markdown',
        'organize_by_category': True
    }
    
    scraper = IntegratedGodOfPromptScraper(config)
    return scraper.run_complete_extraction()


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Análise de argumentos simples
    test_mode = '--test' in sys.argv
    links_only = '--links-only' in sys.argv
    
    print("🚀 GodOfPrompt.ai - Scraper Integrado")
    print("=" * 50)
    
    if links_only:
        print("🔗 Modo: Apenas Links")
        result = run_links_only_extraction(test_mode)
    else:
        print("📝 Modo: Extração Completa")
        result = run_full_extraction(test_mode=test_mode)
    
    if result.get('status') == 'completed':
        print("\n🎉 Execução concluída com sucesso!")
    else:
        print(f"\n⚠️  Execução finalizada com status: {result.get('status')}")