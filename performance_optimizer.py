#!/usr/bin/env python3
"""
Otimizações avançadas de performance para o GodOfPrompt scraper
"""

import asyncio
import concurrent.futures
import threading
import queue
import time
import psutil
import json
import logging
from typing import List, Dict, Optional, Callable, Any
from dataclasses import dataclass, field
from contextlib import contextmanager
import weakref
import gc


@dataclass
class PerformanceMetrics:
    """Métricas detalhadas de performance"""
    
    # Tempos
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    
    # Contadores
    pages_processed: int = 0
    prompts_extracted: int = 0
    categories_completed: int = 0
    errors: int = 0
    retries: int = 0
    
    # Recursos
    peak_memory_mb: float = 0.0
    cpu_usage_samples: List[float] = field(default_factory=list)
    
    # Por categoria
    category_stats: Dict[str, Dict] = field(default_factory=dict)
    
    def record_category_start(self, category: str):
        """Registra início do processamento de uma categoria"""
        self.category_stats[category] = {
            'start_time': time.time(),
            'pages': 0,
            'prompts': 0,
            'errors': 0
        }
    
    def record_category_end(self, category: str):
        """Registra fim do processamento de uma categoria"""
        if category in self.category_stats:
            self.category_stats[category]['end_time'] = time.time()
            self.category_stats[category]['duration'] = (
                self.category_stats[category]['end_time'] - 
                self.category_stats[category]['start_time']
            )
    
    def update_system_resources(self):
        """Atualiza métricas de sistema"""
        # Memória
        memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
        self.peak_memory_mb = max(self.peak_memory_mb, memory_mb)
        
        # CPU
        cpu_percent = psutil.cpu_percent(interval=None)
        self.cpu_usage_samples.append(cpu_percent)
        
        # Limitar amostras de CPU
        if len(self.cpu_usage_samples) > 100:
            self.cpu_usage_samples = self.cpu_usage_samples[-50:]
    
    def get_summary(self) -> Dict:
        """Gera resumo completo das métricas"""
        duration = (self.end_time or time.time()) - self.start_time
        
        return {
            'tempo_total_segundos': round(duration, 2),
            'tempo_formatado': self._format_duration(duration),
            'páginas_processadas': self.pages_processed,
            'prompts_extraídos': self.prompts_extracted,
            'categorias_completadas': self.categories_completed,
            'total_erros': self.errors,
            'total_tentativas': self.retries,
            'taxa_sucesso': f"{((self.pages_processed - self.errors) / max(self.pages_processed, 1)) * 100:.1f}%",
            'performance': {
                'prompts_por_segundo': round(self.prompts_extracted / max(duration, 1), 2),
                'páginas_por_minuto': round(self.pages_processed / max(duration / 60, 1), 1),
                'tempo_médio_por_página': round(duration / max(self.pages_processed, 1), 2)
            },
            'recursos': {
                'pico_memoria_mb': round(self.peak_memory_mb, 1),
                'cpu_médio': round(sum(self.cpu_usage_samples) / max(len(self.cpu_usage_samples), 1), 1) if self.cpu_usage_samples else 0
            },
            'por_categoria': self._get_category_summary()
        }
    
    def _format_duration(self, seconds: float) -> str:
        """Formata duração em formato legível"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds/60:.1f}min"
        else:
            return f"{seconds/3600:.1f}h {(seconds%3600)/60:.0f}min"
    
    def _get_category_summary(self) -> Dict:
        """Resumo por categoria"""
        summary = {}
        for cat, stats in self.category_stats.items():
            if 'duration' in stats:
                summary[cat] = {
                    'tempo': self._format_duration(stats['duration']),
                    'páginas': stats['pages'],
                    'prompts': stats['prompts'],
                    'erros': stats['errors'],
                    'prompts_por_segundo': round(stats['prompts'] / max(stats['duration'], 1), 2)
                }
        return summary


class ResourceManager:
    """Gerenciador inteligente de recursos do sistema"""
    
    def __init__(self, max_memory_mb: int = 1024, max_cpu_percent: int = 80):
        self.max_memory_mb = max_memory_mb
        self.max_cpu_percent = max_cpu_percent
        self.monitoring = False
        self._monitor_thread = None
        
    def start_monitoring(self):
        """Inicia monitoramento de recursos"""
        self.monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitor_resources)
        self._monitor_thread.daemon = True
        self._monitor_thread.start()
        
    def stop_monitoring(self):
        """Para monitoramento de recursos"""
        self.monitoring = False
        if self._monitor_thread:
            self._monitor_thread.join(timeout=1)
    
    def _monitor_resources(self):
        """Thread de monitoramento de recursos"""
        while self.monitoring:
            try:
                # Verificar memória
                memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
                if memory_mb > self.max_memory_mb:
                    logging.warning(f"Uso de memória alto: {memory_mb:.1f}MB")
                    self._trigger_cleanup()
                
                # Verificar CPU
                cpu_percent = psutil.cpu_percent(interval=1)
                if cpu_percent > self.max_cpu_percent:
                    logging.warning(f"Uso de CPU alto: {cpu_percent:.1f}%")
                    time.sleep(2)  # Pausa para reduzir carga
                
                time.sleep(5)  # Monitorar a cada 5 segundos
                
            except Exception as e:
                logging.error(f"Erro no monitoramento de recursos: {e}")
                time.sleep(10)
    
    def _trigger_cleanup(self):
        """Força limpeza de memória"""
        logging.info("Executando limpeza de memória...")
        gc.collect()
        
    @contextmanager
    def resource_guard(self):
        """Context manager para controle de recursos"""
        self.start_monitoring()
        try:
            yield self
        finally:
            self.stop_monitoring()


class BatchProcessor:
    """Processador em lotes para otimizar throughput"""
    
    def __init__(self, batch_size: int = 5, max_workers: int = 3):
        self.batch_size = batch_size
        self.max_workers = max_workers
        self.results_queue = queue.Queue()
        
    def process_categories_parallel(self, categories: List[Dict], 
                                  extract_func: Callable) -> Dict[str, Any]:
        """Processa categorias em paralelo com controle de concorrência"""
        results = {}
        
        # Dividir em lotes
        batches = [categories[i:i + self.batch_size] 
                  for i in range(0, len(categories), self.batch_size)]
        
        for batch_idx, batch in enumerate(batches):
            logging.info(f"Processando lote {batch_idx + 1}/{len(batches)} - {len(batch)} categorias")
            
            # Processar lote em paralelo
            with concurrent.futures.ThreadPoolExecutor(max_workers=min(self.max_workers, len(batch))) as executor:
                # Submeter tarefas
                future_to_category = {
                    executor.submit(extract_func, cat): cat['nome'] 
                    for cat in batch
                }
                
                # Coletar resultados
                for future in concurrent.futures.as_completed(future_to_category, timeout=3600):
                    category_name = future_to_category[future]
                    try:
                        result = future.result()
                        results[category_name] = result
                        logging.info(f"✅ {category_name}: {len(result)} prompts extraídos")
                    except Exception as e:
                        logging.error(f"❌ {category_name}: Erro - {e}")
                        results[category_name] = []
            
            # Pausa entre lotes para evitar sobrecarga
            if batch_idx < len(batches) - 1:
                time.sleep(10)
        
        return results


class CacheManager:
    """Gerenciador de cache inteligente para evitar re-processamento"""
    
    def __init__(self, cache_file: str = "scraper_cache.json"):
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
        
    def _load_cache(self) -> Dict:
        """Carrega cache do arquivo"""
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except Exception as e:
            logging.warning(f"Erro carregando cache: {e}")
            return {}
    
    def save_cache(self):
        """Salva cache no arquivo"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"Erro salvando cache: {e}")
    
    def get_cached_category(self, category_name: str, category_url: str) -> Optional[List]:
        """Recupera categoria do cache se ainda válida"""
        cache_key = f"{category_name}_{hash(category_url)}"
        
        if cache_key in self.cache_data:
            cached_data = self.cache_data[cache_key]
            
            # Verificar se cache ainda é válido (24 horas)
            cache_time = cached_data.get('timestamp', 0)
            if time.time() - cache_time < 86400:  # 24 horas
                logging.info(f"Cache hit para {category_name}")
                return cached_data.get('prompts', [])
        
        return None
    
    def cache_category(self, category_name: str, category_url: str, prompts: List):
        """Armazena categoria no cache"""
        cache_key = f"{category_name}_{hash(category_url)}"
        
        self.cache_data[cache_key] = {
            'prompts': prompts,
            'timestamp': time.time(),
            'count': len(prompts)
        }
        
        # Limitar tamanho do cache (máximo 50 categorias)
        if len(self.cache_data) > 50:
            oldest_key = min(self.cache_data.keys(), 
                           key=lambda k: self.cache_data[k]['timestamp'])
            del self.cache_data[oldest_key]


class ProgressTracker:
    """Rastreador de progresso em tempo real"""
    
    def __init__(self, total_categories: int):
        self.total_categories = total_categories
        self.completed_categories = 0
        self.current_category = ""
        self.start_time = time.time()
        self.category_times = []
        
    def start_category(self, category_name: str):
        """Inicia processamento de categoria"""
        self.current_category = category_name
        self.category_start_time = time.time()
        
        # Calcular ETA
        eta = self._calculate_eta()
        
        logging.info(f"[{self.completed_categories + 1}/{self.total_categories}] "
                    f"Iniciando: {category_name} | ETA: {eta}")
    
    def complete_category(self, prompts_count: int):
        """Completa processamento de categoria"""
        duration = time.time() - self.category_start_time
        self.category_times.append(duration)
        self.completed_categories += 1
        
        logging.info(f"✅ {self.current_category}: {prompts_count} prompts em {duration:.1f}s")
        
    def _calculate_eta(self) -> str:
        """Calcula tempo estimado restante"""
        if not self.category_times:
            return "Calculando..."
        
        avg_time = sum(self.category_times) / len(self.category_times)
        remaining_categories = self.total_categories - self.completed_categories
        estimated_seconds = remaining_categories * avg_time
        
        if estimated_seconds < 60:
            return f"{estimated_seconds:.0f}s"
        elif estimated_seconds < 3600:
            return f"{estimated_seconds/60:.1f}min"
        else:
            return f"{estimated_seconds/3600:.1f}h"
    
    def get_progress_percent(self) -> float:
        """Retorna porcentagem de progresso"""
        return (self.completed_categories / self.total_categories) * 100


class OptimizedScraper:
    """Scraper otimizado com todas as melhorias de performance"""
    
    def __init__(self, config: Dict = None):
        # Configurações padrão otimizadas
        self.config = {
            'batch_size': 3,
            'max_workers': 2,
            'max_memory_mb': 1024,
            'use_cache': True,
            'monitor_resources': True,
            **(config or {})
        }
        
        # Inicializar componentes
        self.metrics = PerformanceMetrics()
        self.resource_manager = ResourceManager(
            max_memory_mb=self.config['max_memory_mb']
        )
        self.batch_processor = BatchProcessor(
            batch_size=self.config['batch_size'],
            max_workers=self.config['max_workers']
        )
        self.cache_manager = CacheManager() if self.config['use_cache'] else None
        
    def extract_all_categories(self, categories: List[Dict], 
                             extract_func: Callable) -> Dict:
        """Extração otimizada de todas as categorias"""
        
        # Filtrar categorias já em cache
        categories_to_process = []
        cached_results = {}
        
        if self.cache_manager:
            for category in categories:
                cached = self.cache_manager.get_cached_category(
                    category['nome'], category['link']
                )
                if cached:
                    cached_results[category['nome']] = cached
                else:
                    categories_to_process.append(category)
        else:
            categories_to_process = categories
        
        logging.info(f"Cache: {len(cached_results)} categorias | "
                    f"Processar: {len(categories_to_process)}")
        
        # Inicializar rastreamento
        progress = ProgressTracker(len(categories_to_process))
        
        # Processar com controle de recursos
        with self.resource_manager.resource_guard():
            # Wrapper para extração com métricas
            def extract_with_metrics(category):
                progress.start_category(category['nome'])
                self.metrics.record_category_start(category['nome'])
                
                try:
                    prompts = extract_func(category)
                    
                    # Atualizar métricas
                    self.metrics.prompts_extracted += len(prompts)
                    self.metrics.category_stats[category['nome']]['prompts'] = len(prompts)
                    
                    # Cache resultado
                    if self.cache_manager:
                        self.cache_manager.cache_category(
                            category['nome'], category['link'], prompts
                        )
                    
                    progress.complete_category(len(prompts))
                    self.metrics.record_category_end(category['nome'])
                    
                    return prompts
                    
                except Exception as e:
                    logging.error(f"Erro processando {category['nome']}: {e}")
                    self.metrics.errors += 1
                    return []
            
            # Processar em lotes paralelos
            processing_results = self.batch_processor.process_categories_parallel(
                categories_to_process, extract_with_metrics
            )
        
        # Combinar resultados
        all_results = {**cached_results, **processing_results}
        
        # Salvar cache
        if self.cache_manager:
            self.cache_manager.save_cache()
        
        # Finalizar métricas
        self.metrics.end_time = time.time()
        self.metrics.categories_completed = len(all_results)
        
        return all_results
    
    def get_performance_report(self) -> Dict:
        """Relatório completo de performance"""
        return self.metrics.get_summary()


# Exemplo de uso
if __name__ == "__main__":
    # Configuração otimizada
    config = {
        'batch_size': 2,
        'max_workers': 2,
        'max_memory_mb': 512,
        'use_cache': True,
        'monitor_resources': True
    }
    
    # Criar scraper otimizado
    scraper = OptimizedScraper(config)
    
    # Exemplo de categorias
    categories = [
        {'nome': 'Marketing', 'link': 'https://example.com/marketing'},
        {'nome': 'Vendas', 'link': 'https://example.com/vendas'}
    ]
    
    # Função de extração mock
    def mock_extract(category):
        time.sleep(2)  # Simular processamento
        return [{'url': f'https://example.com/prompt{i}'} for i in range(10)]
    
    # Executar extração
    results = scraper.extract_all_categories(categories, mock_extract)
    
    # Relatório final
    report = scraper.get_performance_report()
    print(json.dumps(report, indent=2, ensure_ascii=False))