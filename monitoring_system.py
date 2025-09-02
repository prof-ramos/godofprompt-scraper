#!/usr/bin/env python3
"""
Sistema de monitoramento e adaptação em tempo real para o GodOfPrompt scraper
"""

import time
import json
import logging
import threading
import queue
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import psutil
import requests
from datetime import datetime, timedelta


class HealthStatus(Enum):
    """Status de saúde do sistema"""
    HEALTHY = "healthy"
    WARNING = "warning" 
    CRITICAL = "critical"
    BLOCKED = "blocked"


@dataclass
class AlertConfig:
    """Configuração de alertas"""
    
    # Thresholds de performance
    max_error_rate: float = 0.3  # 30% de erro máximo
    min_success_rate: float = 0.7  # 70% de sucesso mínimo
    max_response_time: float = 30.0  # 30s máximo por página
    
    # Thresholds de recursos
    max_memory_usage: int = 1024  # MB
    max_cpu_usage: float = 85.0  # %
    
    # Detecção de bloqueio
    consecutive_errors_threshold: int = 5
    block_keywords: List[str] = field(default_factory=lambda: [
        "blocked", "captcha", "rate limit", "forbidden", 
        "access denied", "too many requests", "bot detection"
    ])


class SystemMonitor:
    """Monitor em tempo real do sistema e performance"""
    
    def __init__(self, alert_config: AlertConfig = None):
        self.config = alert_config or AlertConfig()
        self.is_monitoring = False
        self.monitor_thread = None
        
        # Métricas em tempo real
        self.metrics = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'consecutive_errors': 0,
            'last_error_time': None,
            'response_times': [],
            'memory_usage': [],
            'cpu_usage': [],
            'status': HealthStatus.HEALTHY
        }
        
        # Histórico de alertas
        self.alerts_history = []
        
        # Callbacks para eventos
        self.alert_callbacks: List[Callable] = []
        
    def add_alert_callback(self, callback: Callable[[Dict], None]):
        """Adiciona callback para receber alertas"""
        self.alert_callbacks.append(callback)
        
    def start_monitoring(self):
        """Inicia monitoramento em thread separada"""
        if self.is_monitoring:
            return
            
        self.is_monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
        logging.info("Sistema de monitoramento iniciado")
        
    def stop_monitoring(self):
        """Para o monitoramento"""
        self.is_monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logging.info("Sistema de monitoramento parado")
        
    def record_request(self, success: bool, response_time: float = None, 
                      error_message: str = None):
        """Registra uma requisição para análise"""
        self.metrics['total_requests'] += 1
        
        if success:
            self.metrics['successful_requests'] += 1
            self.metrics['consecutive_errors'] = 0
            
            if response_time:
                self.metrics['response_times'].append(response_time)
                # Manter apenas últimas 100 medições
                if len(self.metrics['response_times']) > 100:
                    self.metrics['response_times'] = self.metrics['response_times'][-50:]
        else:
            self.metrics['failed_requests'] += 1
            self.metrics['consecutive_errors'] += 1
            self.metrics['last_error_time'] = time.time()
            
            # Verificar se é indicativo de bloqueio
            if error_message:
                self._check_for_blocking(error_message)
                
    def get_health_status(self) -> HealthStatus:
        """Avalia status de saúde atual"""
        # Verificar erros consecutivos
        if self.metrics['consecutive_errors'] >= self.config.consecutive_errors_threshold:
            return HealthStatus.BLOCKED
            
        # Verificar taxa de erro
        if self.metrics['total_requests'] > 10:
            error_rate = self.metrics['failed_requests'] / self.metrics['total_requests']
            if error_rate > self.config.max_error_rate:
                return HealthStatus.CRITICAL
            elif error_rate > 0.1:  # 10%
                return HealthStatus.WARNING
        
        # Verificar tempo de resposta
        if self.metrics['response_times']:
            avg_response_time = sum(self.metrics['response_times']) / len(self.metrics['response_times'])
            if avg_response_time > self.config.max_response_time:
                return HealthStatus.WARNING
                
        # Verificar recursos do sistema
        memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
        cpu_usage = psutil.cpu_percent()
        
        if memory_usage > self.config.max_memory_usage or cpu_usage > self.config.max_cpu_usage:
            return HealthStatus.WARNING
            
        return HealthStatus.HEALTHY
        
    def _monitor_loop(self):
        """Loop principal de monitoramento"""
        while self.is_monitoring:
            try:
                # Atualizar status
                old_status = self.metrics['status']
                new_status = self.get_health_status()
                self.metrics['status'] = new_status
                
                # Coletar métricas de sistema
                self._collect_system_metrics()
                
                # Verificar se status mudou
                if old_status != new_status:
                    self._trigger_status_change_alert(old_status, new_status)
                
                # Verificar condições de alerta
                self._check_alert_conditions()
                
                time.sleep(10)  # Monitorar a cada 10 segundos
                
            except Exception as e:
                logging.error(f"Erro no monitoramento: {e}")
                time.sleep(30)  # Esperar mais em caso de erro
                
    def _collect_system_metrics(self):
        """Coleta métricas do sistema"""
        try:
            # Memória
            memory_mb = psutil.Process().memory_info().rss / 1024 / 1024
            self.metrics['memory_usage'].append(memory_mb)
            
            # CPU
            cpu_percent = psutil.cpu_percent()
            self.metrics['cpu_usage'].append(cpu_percent)
            
            # Limitar histórico
            for key in ['memory_usage', 'cpu_usage']:
                if len(self.metrics[key]) > 100:
                    self.metrics[key] = self.metrics[key][-50:]
                    
        except Exception as e:
            logging.error(f"Erro coletando métricas: {e}")
            
    def _check_for_blocking(self, error_message: str):
        """Verifica se mensagem de erro indica bloqueio"""
        error_lower = error_message.lower()
        for keyword in self.config.block_keywords:
            if keyword in error_lower:
                self._trigger_alert("BLOQUEIO_DETECTADO", {
                    'keyword': keyword,
                    'error_message': error_message,
                    'consecutive_errors': self.metrics['consecutive_errors']
                })
                break
                
    def _check_alert_conditions(self):
        """Verifica condições que podem gerar alertas"""
        # Alta taxa de erro sustentada
        if self.metrics['total_requests'] > 20:
            error_rate = self.metrics['failed_requests'] / self.metrics['total_requests']
            if error_rate > 0.5:  # 50% de erro
                self._trigger_alert("ALTA_TAXA_ERRO", {
                    'error_rate': error_rate,
                    'total_requests': self.metrics['total_requests'],
                    'failed_requests': self.metrics['failed_requests']
                })
        
        # Tempo de resposta muito alto
        if self.metrics['response_times']:
            recent_times = self.metrics['response_times'][-10:]  # Últimas 10
            avg_time = sum(recent_times) / len(recent_times)
            if avg_time > self.config.max_response_time:
                self._trigger_alert("RESPOSTA_LENTA", {
                    'avg_response_time': avg_time,
                    'threshold': self.config.max_response_time
                })
        
        # Uso excessivo de recursos
        if self.metrics['memory_usage']:
            current_memory = self.metrics['memory_usage'][-1]
            if current_memory > self.config.max_memory_usage:
                self._trigger_alert("MEMORIA_ALTA", {
                    'current_memory_mb': current_memory,
                    'threshold_mb': self.config.max_memory_usage
                })
                
    def _trigger_status_change_alert(self, old_status: HealthStatus, new_status: HealthStatus):
        """Dispara alerta de mudança de status"""
        self._trigger_alert("MUDANCA_STATUS", {
            'old_status': old_status.value,
            'new_status': new_status.value,
            'timestamp': datetime.now().isoformat()
        })
        
    def _trigger_alert(self, alert_type: str, details: Dict):
        """Dispara um alerta"""
        alert = {
            'type': alert_type,
            'timestamp': datetime.now().isoformat(),
            'details': details,
            'metrics_snapshot': self._get_metrics_snapshot()
        }
        
        # Adicionar ao histórico
        self.alerts_history.append(alert)
        
        # Limitar histórico
        if len(self.alerts_history) > 100:
            self.alerts_history = self.alerts_history[-50:]
        
        # Notificar callbacks
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                logging.error(f"Erro em callback de alerta: {e}")
        
        # Log do alerta
        logging.warning(f"ALERTA [{alert_type}]: {details}")
        
    def _get_metrics_snapshot(self) -> Dict:
        """Gera snapshot das métricas atuais"""
        return {
            'status': self.metrics['status'].value,
            'total_requests': self.metrics['total_requests'],
            'success_rate': self._calculate_success_rate(),
            'consecutive_errors': self.metrics['consecutive_errors'],
            'avg_response_time': self._calculate_avg_response_time(),
            'memory_usage_mb': self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0,
            'cpu_usage_percent': self.metrics['cpu_usage'][-1] if self.metrics['cpu_usage'] else 0
        }
        
    def _calculate_success_rate(self) -> float:
        """Calcula taxa de sucesso atual"""
        if self.metrics['total_requests'] == 0:
            return 1.0
        return self.metrics['successful_requests'] / self.metrics['total_requests']
        
    def _calculate_avg_response_time(self) -> float:
        """Calcula tempo médio de resposta"""
        if not self.metrics['response_times']:
            return 0.0
        return sum(self.metrics['response_times']) / len(self.metrics['response_times'])
        
    def get_dashboard_data(self) -> Dict:
        """Retorna dados para dashboard de monitoramento"""
        return {
            'status': self.metrics['status'].value,
            'uptime_seconds': time.time() - (self.metrics.get('start_time', time.time())),
            'performance': {
                'total_requests': self.metrics['total_requests'],
                'success_rate': self._calculate_success_rate(),
                'error_rate': 1 - self._calculate_success_rate(),
                'avg_response_time': self._calculate_avg_response_time(),
                'consecutive_errors': self.metrics['consecutive_errors']
            },
            'resources': {
                'memory_usage_mb': self.metrics['memory_usage'][-1] if self.metrics['memory_usage'] else 0,
                'cpu_usage_percent': self.metrics['cpu_usage'][-1] if self.metrics['cpu_usage'] else 0,
                'memory_history': self.metrics['memory_usage'][-20:],
                'cpu_history': self.metrics['cpu_usage'][-20:]
            },
            'recent_alerts': self.alerts_history[-10:],
            'recommendations': self._get_recommendations()
        }
        
    def _get_recommendations(self) -> List[str]:
        """Gera recomendações baseadas no estado atual"""
        recommendations = []
        
        # Baseado no status
        if self.metrics['status'] == HealthStatus.BLOCKED:
            recommendations.extend([
                "Sistema possivelmente bloqueado - considere trocar IP/proxy",
                "Aumentar delays entre requisições",
                "Verificar se headers estão sendo detectados"
            ])
        elif self.metrics['status'] == HealthStatus.CRITICAL:
            recommendations.extend([
                "Alta taxa de erro - reduzir velocidade de scraping",
                "Verificar logs para padrões de erro",
                "Considerar usar diferentes User-Agents"
            ])
        elif self.metrics['status'] == HealthStatus.WARNING:
            recommendations.append("Monitorar de perto - possíveis problemas surgindo")
            
        # Baseado em métricas específicas
        if self.metrics['memory_usage'] and self.metrics['memory_usage'][-1] > 800:
            recommendations.append("Uso de memória alto - executar limpeza")
            
        if self.metrics['consecutive_errors'] > 3:
            recommendations.append("Muitos erros consecutivos - considerar pausa")
            
        return recommendations


class AdaptiveController:
    """Controlador que adapta comportamento baseado no monitoramento"""
    
    def __init__(self, monitor: SystemMonitor):
        self.monitor = monitor
        self.adaptations_applied = []
        
        # Configurações adaptativas
        self.base_delay = 2.0
        self.current_delay_multiplier = 1.0
        self.max_delay_multiplier = 8.0
        
        # Registrar callback no monitor
        self.monitor.add_alert_callback(self._handle_alert)
        
    def get_adaptive_delay(self) -> float:
        """Retorna delay adaptativo baseado no status atual"""
        base = self.base_delay * self.current_delay_multiplier
        
        # Ajustar baseado no status
        status = self.monitor.get_health_status()
        if status == HealthStatus.BLOCKED:
            return base * 4  # Muito mais lento quando bloqueado
        elif status == HealthStatus.CRITICAL:
            return base * 2  # Mais lento quando crítico
        elif status == HealthStatus.WARNING:
            return base * 1.5  # Um pouco mais lento
        else:
            return base
            
    def should_pause_scraping(self) -> bool:
        """Decide se deve pausar o scraping"""
        status = self.monitor.get_health_status()
        
        # Pausar se bloqueado ou muitos erros consecutivos
        if status == HealthStatus.BLOCKED:
            return True
            
        if self.monitor.metrics['consecutive_errors'] >= 10:
            return True
            
        return False
        
    def get_recommended_user_agent(self) -> Optional[str]:
        """Recomenda troca de User-Agent se necessário"""
        if self.monitor.metrics['consecutive_errors'] >= 5:
            # Lista de User-Agents alternativos
            user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
                "Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0"
            ]
            return user_agents[self.monitor.metrics['consecutive_errors'] % len(user_agents)]
        return None
        
    def _handle_alert(self, alert: Dict):
        """Manuseia alertas do sistema de monitoramento"""
        alert_type = alert['type']
        
        if alert_type == "ALTA_TAXA_ERRO":
            # Aumentar delay
            self.current_delay_multiplier = min(
                self.current_delay_multiplier * 1.5, 
                self.max_delay_multiplier
            )
            self.adaptations_applied.append(f"Delay aumentado para {self.current_delay_multiplier}x")
            
        elif alert_type == "BLOQUEIO_DETECTADO":
            # Aumentar delay drasticamente
            self.current_delay_multiplier = self.max_delay_multiplier
            self.adaptations_applied.append("Delay máximo aplicado - bloqueio detectado")
            
        elif alert_type == "RESPOSTA_LENTA":
            # Diminuir concorrência (se aplicável)
            self.adaptations_applied.append("Sistema lento detectado")


# Exemplo de integração
def create_monitoring_system():
    """Cria sistema completo de monitoramento"""
    
    # Configuração de alertas
    alert_config = AlertConfig(
        max_error_rate=0.25,
        min_success_rate=0.75,
        max_response_time=25.0,
        consecutive_errors_threshold=5
    )
    
    # Criar monitor
    monitor = SystemMonitor(alert_config)
    
    # Criar controlador adaptativo
    controller = AdaptiveController(monitor)
    
    # Callback personalizado para logs
    def log_alert(alert):
        logging.warning(f"🚨 ALERTA: {alert['type']} - {alert['details']}")
    
    monitor.add_alert_callback(log_alert)
    
    return {
        'monitor': monitor,
        'controller': controller,
        'start': lambda: monitor.start_monitoring(),
        'stop': lambda: monitor.stop_monitoring(),
        'dashboard': lambda: monitor.get_dashboard_data()
    }


if __name__ == "__main__":
    # Teste do sistema de monitoramento
    logging.basicConfig(level=logging.INFO)
    
    system = create_monitoring_system()
    system['start']()
    
    try:
        # Simular algumas requisições
        for i in range(20):
            success = i % 4 != 0  # 75% de sucesso
            response_time = 5.0 if success else 30.0
            
            system['monitor'].record_request(success, response_time, 
                                           "Error 429" if not success else None)
            time.sleep(1)
        
        # Ver dashboard
        dashboard = system['dashboard']()
        print(json.dumps(dashboard, indent=2, ensure_ascii=False))
        
    finally:
        system['stop']()