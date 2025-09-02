#!/usr/bin/env python3
"""
Sistema de armazenamento inteligente para prompts e links do GodOfPrompt.ai
Organiza dados em estrutura hierárquica com fallback para diferentes formatos
"""

import os
import json
import yaml
import time
import logging
import re
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
from datetime import datetime


@dataclass
class StorageConfig:
    """Configuração do sistema de armazenamento"""
    
    # Diretórios principais
    base_dir: str = "godofprompt_data"
    prompts_dir: str = "prompts"
    links_dir: str = "links"
    metadata_dir: str = "metadata"
    
    # Organização por categoria
    organize_by_category: bool = True
    
    # Formatos de arquivo
    prompt_format: str = "markdown"  # markdown, json, txt
    links_format: str = "yaml"       # yaml, json
    
    # Nomenclatura
    sanitize_filenames: bool = True
    max_filename_length: int = 100
    
    # Backup e versionamento
    create_backups: bool = True
    max_backups: int = 5
    
    def __post_init__(self):
        # Criar diretórios se não existirem
        for dir_name in [self.base_dir, 
                        os.path.join(self.base_dir, self.prompts_dir),
                        os.path.join(self.base_dir, self.links_dir),
                        os.path.join(self.base_dir, self.metadata_dir)]:
            Path(dir_name).mkdir(parents=True, exist_ok=True)


class FileManager:
    """Gerenciador de arquivos com utilitários de organização"""
    
    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.setup_directories()
        
    def setup_directories(self):
        """Cria estrutura de diretórios"""
        base_path = Path(self.config.base_dir)
        
        # Diretórios principais
        (base_path / self.config.prompts_dir).mkdir(exist_ok=True)
        (base_path / self.config.links_dir).mkdir(exist_ok=True)
        (base_path / self.config.metadata_dir).mkdir(exist_ok=True)
        
        # Subdiretórios para categorias (se habilitado)
        if self.config.organize_by_category:
            categories = ["vendas", "educacao", "empreendedores", "seo", 
                         "produtividade", "escrita", "negocios", "marketing"]
            
            for category in categories:
                (base_path / self.config.prompts_dir / category).mkdir(exist_ok=True)
        
        logging.info(f"Estrutura de diretórios criada em: {self.config.base_dir}")
    
    def sanitize_filename(self, filename: str) -> str:
        """Sanitiza nome de arquivo para compatibilidade"""
        if not self.config.sanitize_filenames:
            return filename
        
        # Remover caracteres problemáticos
        filename = re.sub(r'[^\w\-_\.]', '_', filename)
        
        # Remover underscores múltiplos
        filename = re.sub(r'_+', '_', filename)
        
        # Limitar comprimento
        if len(filename) > self.config.max_filename_length:
            name, ext = os.path.splitext(filename)
            max_name_len = self.config.max_filename_length - len(ext)
            filename = name[:max_name_len] + ext
        
        return filename.strip('_')
    
    def generate_unique_filename(self, base_name: str, directory: str, 
                                extension: str = "") -> str:
        """Gera nome de arquivo único"""
        base_name = self.sanitize_filename(base_name)
        
        # Adicionar extensão se não presente
        if extension and not base_name.endswith(extension):
            base_name += extension
        
        file_path = Path(directory) / base_name
        
        # Se arquivo não existe, retornar nome original
        if not file_path.exists():
            return base_name
        
        # Gerar nome único com contador
        name, ext = os.path.splitext(base_name)
        counter = 1
        
        while file_path.exists():
            new_name = f"{name}_{counter}{ext}"
            file_path = Path(directory) / new_name
            counter += 1
        
        return file_path.name
    
    def create_backup(self, file_path: str) -> Optional[str]:
        """Cria backup de arquivo existente"""
        if not self.config.create_backups or not os.path.exists(file_path):
            return None
        
        # Diretório de backup
        backup_dir = Path(file_path).parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        # Nome do backup com timestamp
        original_name = Path(file_path).stem
        extension = Path(file_path).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{original_name}_backup_{timestamp}{extension}"
        
        backup_path = backup_dir / backup_name
        
        try:
            # Copiar arquivo
            import shutil
            shutil.copy2(file_path, backup_path)
            
            # Limitar número de backups
            self._cleanup_old_backups(backup_dir, original_name)
            
            logging.info(f"Backup criado: {backup_path}")
            return str(backup_path)
            
        except Exception as e:
            logging.error(f"Erro criando backup: {e}")
            return None
    
    def _cleanup_old_backups(self, backup_dir: Path, base_name: str):
        """Remove backups antigos mantendo apenas os mais recentes"""
        pattern = f"{base_name}_backup_*"
        backups = sorted(backup_dir.glob(pattern), key=os.path.getmtime)
        
        # Remover backups em excesso
        while len(backups) > self.config.max_backups:
            old_backup = backups.pop(0)
            try:
                old_backup.unlink()
                logging.debug(f"Backup antigo removido: {old_backup}")
            except Exception as e:
                logging.error(f"Erro removendo backup antigo: {e}")


class PromptStorage:
    """Sistema de armazenamento para prompts completos"""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.config = file_manager.config
        
    def save_prompt(self, prompt_data: Dict[str, Any]) -> str:
        """Salva prompt individual em arquivo"""
        
        # Extrair informações básicas
        prompt_id = prompt_data.get('id', 'unknown')
        title = prompt_data.get('title', prompt_id)
        category = prompt_data.get('category', 'uncategorized').lower()
        
        # Determinar diretório
        if self.config.organize_by_category:
            prompt_dir = os.path.join(
                self.config.base_dir, 
                self.config.prompts_dir, 
                self._normalize_category(category)
            )
        else:
            prompt_dir = os.path.join(self.config.base_dir, self.config.prompts_dir)
        
        Path(prompt_dir).mkdir(parents=True, exist_ok=True)
        
        # Nome do arquivo baseado no título e ID
        base_filename = f"{prompt_id}_{title}"
        
        # Salvar baseado no formato configurado
        if self.config.prompt_format == "markdown":
            return self._save_as_markdown(prompt_data, prompt_dir, base_filename)
        elif self.config.prompt_format == "json":
            return self._save_as_json(prompt_data, prompt_dir, base_filename)
        else:  # txt
            return self._save_as_text(prompt_data, prompt_dir, base_filename)
    
    def _save_as_markdown(self, prompt_data: Dict, directory: str, base_name: str) -> str:
        """Salva prompt em formato Markdown"""
        filename = self.file_manager.generate_unique_filename(base_name, directory, ".md")
        file_path = os.path.join(directory, filename)
        
        # Criar backup se arquivo existe
        self.file_manager.create_backup(file_path)
        
        # Conteúdo Markdown
        content_parts = []
        
        # Cabeçalho
        title = prompt_data.get('title', 'Sem Título')
        content_parts.append(f"# {title}\n")
        
        # Metadados
        content_parts.append("## 📋 Metadados\n")
        content_parts.append(f"- **ID**: {prompt_data.get('id', 'N/A')}")
        content_parts.append(f"- **Categoria**: {prompt_data.get('category', 'N/A')}")
        content_parts.append(f"- **URL**: {prompt_data.get('url', 'N/A')}")
        
        if prompt_data.get('tags'):
            tags_str = ", ".join(prompt_data['tags'])
            content_parts.append(f"- **Tags**: {tags_str}")
        
        content_parts.append(f"- **Extraído em**: {prompt_data.get('extracted_at', 'N/A')}")
        content_parts.append(f"- **Tokens Estimados**: {prompt_data.get('estimated_tokens', 'N/A')}")
        
        if prompt_data.get('difficulty'):
            content_parts.append(f"- **Dificuldade**: {prompt_data.get('difficulty')}")
        
        content_parts.append("")  # Linha em branco
        
        # Descrição
        if prompt_data.get('description'):
            content_parts.append("## 📝 Descrição\n")
            content_parts.append(prompt_data['description'])
            content_parts.append("")
        
        # Conteúdo principal do prompt
        if prompt_data.get('prompt_text'):
            content_parts.append("## 🎯 Prompt\n")
            content_parts.append("```")
            content_parts.append(prompt_data['prompt_text'])
            content_parts.append("```")
            content_parts.append("")
        
        # Instruções (se houver)
        if prompt_data.get('instructions'):
            content_parts.append("## 📖 Instruções\n")
            content_parts.append(prompt_data['instructions'])
            content_parts.append("")
        
        # Casos de uso
        if prompt_data.get('use_cases'):
            content_parts.append("## 💡 Casos de Uso\n")
            for i, use_case in enumerate(prompt_data['use_cases'], 1):
                content_parts.append(f"{i}. {use_case}")
            content_parts.append("")
        
        # Informações técnicas
        content_parts.append("## 🔧 Informações Técnicas\n")
        content_parts.append(f"- **Método de Extração**: {prompt_data.get('extraction_method', 'N/A')}")
        content_parts.append(f"- **Status**: {'✅ Sucesso' if prompt_data.get('success') else '❌ Falha'}")
        
        if prompt_data.get('error_message'):
            content_parts.append(f"- **Erro**: {prompt_data['error_message']}")
        
        # Escrever arquivo
        markdown_content = "\n".join(content_parts)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            logging.info(f"Prompt salvo em Markdown: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Erro salvando prompt em Markdown: {e}")
            raise
    
    def _save_as_json(self, prompt_data: Dict, directory: str, base_name: str) -> str:
        """Salva prompt em formato JSON"""
        filename = self.file_manager.generate_unique_filename(base_name, directory, ".json")
        file_path = os.path.join(directory, filename)
        
        # Criar backup se arquivo existe
        self.file_manager.create_backup(file_path)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(prompt_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Prompt salvo em JSON: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Erro salvando prompt em JSON: {e}")
            raise
    
    def _save_as_text(self, prompt_data: Dict, directory: str, base_name: str) -> str:
        """Salva prompt em formato texto simples"""
        filename = self.file_manager.generate_unique_filename(base_name, directory, ".txt")
        file_path = os.path.join(directory, filename)
        
        # Criar backup se arquivo existe
        self.file_manager.create_backup(file_path)
        
        # Conteúdo em texto
        content_parts = []
        
        content_parts.append(f"TÍTULO: {prompt_data.get('title', 'Sem Título')}")
        content_parts.append(f"ID: {prompt_data.get('id', 'N/A')}")
        content_parts.append(f"CATEGORIA: {prompt_data.get('category', 'N/A')}")
        content_parts.append(f"URL: {prompt_data.get('url', 'N/A')}")
        content_parts.append(f"EXTRAÍDO EM: {prompt_data.get('extracted_at', 'N/A')}")
        content_parts.append("")
        
        if prompt_data.get('description'):
            content_parts.append("DESCRIÇÃO:")
            content_parts.append(prompt_data['description'])
            content_parts.append("")
        
        if prompt_data.get('prompt_text'):
            content_parts.append("PROMPT:")
            content_parts.append(prompt_data['prompt_text'])
            content_parts.append("")
        
        if prompt_data.get('tags'):
            content_parts.append(f"TAGS: {', '.join(prompt_data['tags'])}")
        
        text_content = "\n".join(content_parts)
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text_content)
            
            logging.info(f"Prompt salvo em TXT: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Erro salvando prompt em TXT: {e}")
            raise
    
    def _normalize_category(self, category: str) -> str:
        """Normaliza nome da categoria para uso como diretório"""
        # Mapeamento de categorias conhecidas
        category_map = {
            'vendas': 'vendas',
            'educação': 'educacao', 
            'educacao': 'educacao',
            'empreendedores individuais': 'empreendedores',
            'empreendedores': 'empreendedores',
            'seo': 'seo',
            'produtividade': 'produtividade',
            'escrita': 'escrita',
            'negócios': 'negocios',
            'negocios': 'negocios',
            'marketing': 'marketing'
        }
        
        normalized = category.lower().strip()
        return category_map.get(normalized, self.file_manager.sanitize_filename(normalized))
    
    def save_multiple_prompts(self, prompts_data: List[Dict]) -> List[str]:
        """Salva múltiplos prompts"""
        saved_files = []
        
        logging.info(f"Salvando {len(prompts_data)} prompts...")
        
        for i, prompt_data in enumerate(prompts_data, 1):
            try:
                file_path = self.save_prompt(prompt_data)
                saved_files.append(file_path)
                
                if i % 10 == 0:
                    logging.info(f"Progresso: {i}/{len(prompts_data)} prompts salvos")
                    
            except Exception as e:
                logging.error(f"Erro salvando prompt {i}: {e}")
                continue
        
        logging.info(f"✅ {len(saved_files)} prompts salvos com sucesso")
        return saved_files


class LinksStorage:
    """Sistema de armazenamento para links (fallback)"""
    
    def __init__(self, file_manager: FileManager):
        self.file_manager = file_manager
        self.config = file_manager.config
    
    def save_links_by_category(self, links_data: Dict[str, List[Dict]]) -> str:
        """Salva links organizados por categoria em YAML único"""
        
        links_dir = os.path.join(self.config.base_dir, self.config.links_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if self.config.links_format == "yaml":
            filename = f"todos_os_links_{timestamp}.yaml"
            return self._save_as_yaml(links_data, links_dir, filename)
        else:
            filename = f"todos_os_links_{timestamp}.json"
            return self._save_as_json_links(links_data, links_dir, filename)
    
    def _save_as_yaml(self, links_data: Dict, directory: str, filename: str) -> str:
        """Salva links em formato YAML"""
        file_path = os.path.join(directory, filename)
        
        # Criar backup se arquivo existe
        self.file_manager.create_backup(file_path)
        
        # Estrutura YAML organizada
        yaml_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_categories': len(links_data),
                'total_links': sum(len(links) for links in links_data.values()),
                'extraction_info': 'Links extraídos do GodOfPrompt.ai'
            },
            'categories': {}
        }
        
        for category, links in links_data.items():
            yaml_data['categories'][category] = {
                'count': len(links),
                'links': links
            }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(yaml_data, f, default_flow_style=False, 
                         allow_unicode=True, indent=2, sort_keys=False)
            
            logging.info(f"Links salvos em YAML: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Erro salvando links em YAML: {e}")
            raise
    
    def _save_as_json_links(self, links_data: Dict, directory: str, filename: str) -> str:
        """Salva links em formato JSON"""
        file_path = os.path.join(directory, filename)
        
        # Criar backup se arquivo existe
        self.file_manager.create_backup(file_path)
        
        # Estrutura JSON
        json_data = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'total_categories': len(links_data),
                'total_links': sum(len(links) for links in links_data.values()),
                'extraction_info': 'Links extraídos do GodOfPrompt.ai'
            },
            'categories': links_data
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Links salvos em JSON: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Erro salvando links em JSON: {e}")
            raise


class StorageManager:
    """Gerenciador principal do sistema de armazenamento"""
    
    def __init__(self, config: StorageConfig = None):
        self.config = config or StorageConfig()
        self.file_manager = FileManager(self.config)
        self.prompt_storage = PromptStorage(self.file_manager)
        self.links_storage = LinksStorage(self.file_manager)
    
    def save_extraction_results(self, results: Dict[str, Any]) -> Dict[str, str]:
        """Salva resultados da extração no formato apropriado"""
        
        saved_files = {'metadata': [], 'prompts': [], 'links': []}
        
        # Se temos prompts completos, salvar individualmente
        if 'prompts' in results and results['prompts']:
            logging.info("Salvando prompts completos em arquivos individuais...")
            
            prompt_files = self.prompt_storage.save_multiple_prompts(results['prompts'])
            saved_files['prompts'] = prompt_files
            
            # Salvar também metadados em JSON
            metadata_file = self._save_metadata(results)
            saved_files['metadata'].append(metadata_file)
            
        # Se temos apenas links, salvar em YAML/JSON
        elif 'links_by_category' in results:
            logging.info("Salvando links em arquivo único...")
            
            links_file = self.links_storage.save_links_by_category(results['links_by_category'])
            saved_files['links'].append(links_file)
            
            # Salvar metadados
            metadata_file = self._save_metadata(results)
            saved_files['metadata'].append(metadata_file)
        
        return saved_files
    
    def _save_metadata(self, results: Dict[str, Any]) -> str:
        """Salva metadados da extração"""
        metadata_dir = os.path.join(self.config.base_dir, self.config.metadata_dir)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"extraction_metadata_{timestamp}.json"
        file_path = os.path.join(metadata_dir, filename)
        
        # Extrair apenas metadados (sem conteúdo completo)
        metadata = {
            'extraction_info': results.get('extraction_info', {}),
            'statistics': results.get('statistics', {}),
            'generated_at': datetime.now().isoformat(),
            'storage_config': asdict(self.config)
        }
        
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            
            logging.info(f"Metadados salvos: {file_path}")
            return file_path
            
        except Exception as e:
            logging.error(f"Erro salvando metadados: {e}")
            raise
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """Retorna estatísticas do armazenamento"""
        base_path = Path(self.config.base_dir)
        
        stats = {
            'total_files': 0,
            'prompts_count': 0,
            'links_files': 0,
            'total_size_mb': 0,
            'categories': {}
        }
        
        try:
            # Contar arquivos de prompts
            prompts_path = base_path / self.config.prompts_dir
            if prompts_path.exists():
                for file_path in prompts_path.rglob('*'):
                    if file_path.is_file():
                        stats['prompts_count'] += 1
                        stats['total_files'] += 1
                        stats['total_size_mb'] += file_path.stat().st_size / (1024 * 1024)
            
            # Contar arquivos de links
            links_path = base_path / self.config.links_dir
            if links_path.exists():
                stats['links_files'] = len([f for f in links_path.iterdir() if f.is_file()])
                stats['total_files'] += stats['links_files']
            
            # Estatísticas por categoria
            if self.config.organize_by_category:
                for category_dir in prompts_path.iterdir():
                    if category_dir.is_dir():
                        category_files = len([f for f in category_dir.iterdir() if f.is_file()])
                        if category_files > 0:
                            stats['categories'][category_dir.name] = category_files
            
            stats['total_size_mb'] = round(stats['total_size_mb'], 2)
            
        except Exception as e:
            logging.error(f"Erro calculando estatísticas: {e}")
        
        return stats


# Função de conveniência para uso fácil
def create_storage_system(organize_by_category: bool = True, 
                         prompt_format: str = "markdown") -> StorageManager:
    """Cria sistema de armazenamento com configurações otimizadas"""
    
    config = StorageConfig(
        organize_by_category=organize_by_category,
        prompt_format=prompt_format,
        create_backups=True,
        max_backups=3
    )
    
    return StorageManager(config)


# Exemplo de uso
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Criar sistema de armazenamento
    storage = create_storage_system()
    
    # Dados de exemplo
    sample_prompt = {
        'id': 'marketing-001',
        'title': 'Estratégia de Marketing Digital',
        'category': 'Marketing',
        'url': 'https://example.com/prompt/marketing-001',
        'prompt_text': 'Crie uma estratégia de marketing digital para...',
        'description': 'Prompt para criação de estratégias de marketing',
        'tags': ['marketing', 'digital', 'estratégia'],
        'extracted_at': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'success': True,
        'estimated_tokens': 250
    }
    
    # Salvar prompt
    file_path = storage.prompt_storage.save_prompt(sample_prompt)
    print(f"Prompt salvo em: {file_path}")
    
    # Mostrar estatísticas
    stats = storage.get_storage_stats()
    print(f"Estatísticas: {stats}")