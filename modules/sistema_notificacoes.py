#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de sistema de notificações para o ConcursAI"""

import pandas as pd
import smtplib
try:
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False
    print("⚠️ Email não disponível neste ambiente")
from datetime import datetime, timedelta
import json
import os
from typing import List, Dict

class SistemaNotificacoes:
    """Sistema de notificações para novos concursos"""
    
    def __init__(self):
        self.config_file = "config_notificacoes.json"
        self.historico_file = "historico_notificacoes.json"
        self.load_config()
    
    def load_config(self):
        """Carrega configurações de notificação"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            else:
                self.config = self.criar_config_padrao()
                self.salvar_config()
        except Exception as e:
            print(f"⚠️ Erro ao carregar config: {e}")
            self.config = self.criar_config_padrao()
    
    def criar_config_padrao(self) -> Dict:
        """Cria configuração padrão"""
        return {
            "email": {
                "habilitado": False,
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "email_remetente": "",
                "senha_remetente": "",
                "emails_destino": []
            },
            "filtros": {
                "orgaos_interesse": ["PREFEITURA", "TRIBUNAL", "MINISTÉRIO"],
                "cargos_interesse": ["ANALISTA", "TÉCNICO"],
                "estados_interesse": ["SP", "RJ", "MG"],
                "salario_minimo": 3000
            },
            "frequencia_verificacao": 24  # horas
        }
    
    def salvar_config(self):
        """Salva configurações"""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao salvar config: {e}")
    
    def configurar_email(self, smtp_server: str, smtp_port: int, email: str, senha: str, destinatarios: List[str]):
        """Configura parâmetros de email"""
        self.config["email"]["smtp_server"] = smtp_server
        self.config["email"]["smtp_port"] = smtp_port
        self.config["email"]["email_remetente"] = email
        self.config["email"]["senha_remetente"] = senha
        self.config["email"]["emails_destino"] = destinatarios
        self.config["email"]["habilitado"] = True
        self.salvar_config()
        print("✅ Configuração de email salva")
    
    def configurar_filtros(self, orgaos: List[str] = None, cargos: List[str] = None, 
                          estados: List[str] = None, salario_min: float = None):
        """Configura filtros de interesse"""
        if orgaos:
            self.config["filtros"]["orgaos_interesse"] = orgaos
        if cargos:
            self.config["filtros"]["cargos_interesse"] = cargos
        if estados:
            self.config["filtros"]["estados_interesse"] = estados
        if salario_min:
            self.config["filtros"]["salario_minimo"] = salario_min
        
        self.salvar_config()
        print("✅ Filtros configurados")
    
    def verificar_novos_concursos(self, arquivo_concursos: str = "concursos_chunks.csv") -> List[Dict]:
        """Verifica novos concursos baseado nos filtros"""
        try:
            if not os.path.exists(arquivo_concursos):
                return []
            
            df = pd.read_csv(arquivo_concursos)
            
            # Carregar histórico
            historico = self.carregar_historico()
            concursos_conhecidos = set(historico.get("concursos_notificados", []))
            
            # Filtrar concursos de interesse
            concursos_interessantes = []
            
            for _, row in df.iterrows():
                titulo = str(row.get('titulo', ''))
                orgao = str(row.get('orgao', ''))
                cargo = str(row.get('cargo', ''))
                
                # Verificar se já foi notificado
                if titulo in concursos_conhecidos:
                    continue
                
                # Aplicar filtros
                if self._aplicar_filtros(row):
                    concursos_interessantes.append({
                        'titulo': titulo,
                        'orgao': orgao,
                        'cargo': cargo,
                        'salario': row.get('salario', 'Não informado'),
                        'vagas': row.get('vagas', 'Não informado'),
                        'url': row.get('url', ''),
                        'data_coleta': row.get('data_publicacao', '')
                    })
                    concursos_conhecidos.add(titulo)
            
            # Atualizar histórico
            if concursos_interessantes:
                self.atualizar_historico(list(concursos_conhecidos))
            
            return concursos_interessantes
            
        except Exception as e:
            print(f"❌ Erro ao verificar concursos: {e}")
            return []
    
    def _aplicar_filtros(self, row) -> bool:
        """Aplica filtros para determinar se concurso é de interesse"""
        orgao = str(row.get('orgao', '')).upper()
        cargo = str(row.get('cargo', '')).upper()
        titulo = str(row.get('titulo', '')).upper()
        
        # Se os filtros estão vazios ou com valores padrão, considerar tudo como interessante
        orgaos_interesse = self.config["filtros"]["orgaos_interesse"]
        cargos_interesse = self.config["filtros"]["cargos_interesse"]
        
        if not orgaos_interesse or orgaos_interesse == ["PREFEITURA", "TRIBUNAL", "MINISTÉRIO"]:
            # Filtros padrão - aceitar tudo
            return True
        
        # Filtro por órgão (busca parcial)
        orgaos_interesse_upper = [o.upper() for o in orgaos_interesse]
        if orgaos_interesse_upper:
            if not any(org in orgao or org in titulo for org in orgaos_interesse_upper):
                return False
        
        # Filtro por cargo (busca parcial)
        cargos_interesse_upper = [c.upper() for c in cargos_interesse]
        if cargos_interesse_upper and cargos_interesse != ["ANALISTA", "TÉCNICO", "PROFESSOR"]:
            if not any(cargo_int in cargo or cargo_int in titulo for cargo_int in cargos_interesse_upper):
                return False
        
        # Filtro por salário (se disponível)
        salario_str = str(row.get('salario', ''))
        if salario_str and 'R$' in salario_str:
            try:
                import re
                salario_num = re.findall(r'[\d.,]+', salario_str.replace('.', '').replace(',', '.'))
                if salario_num:
                    salario_valor = float(salario_num[0])
                    if salario_valor < self.config["filtros"]["salario_minimo"]:
                        return False
            except:
                pass
        
        return True
    
    def carregar_historico(self) -> Dict:
        """Carrega histórico de notificações"""
        try:
            if os.path.exists(self.historico_file):
                with open(self.historico_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {"concursos_notificados": [], "ultima_verificacao": ""}
        except:
            return {"concursos_notificados": [], "ultima_verificacao": ""}
    
    def atualizar_historico(self, concursos_notificados: List[str]):
        """Atualiza histórico de notificações"""
        try:
            historico = {
                "concursos_notificados": concursos_notificados,
                "ultima_verificacao": datetime.now().isoformat()
            }
            with open(self.historico_file, 'w', encoding='utf-8') as f:
                json.dump(historico, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Erro ao atualizar histórico: {e}")
    
    def enviar_notificacao_email(self, concursos: List[Dict]):
        """Envia notificação por email"""
        if not self.config["email"]["habilitado"] or not concursos:
            return False
        
        if not EMAIL_AVAILABLE:
            print("⚠️ Sistema de email não disponível. Use notificações de desktop.")
            return False
        
        try:
            # Preparar conteúdo do email
            assunto = f"🎯 {len(concursos)} novos concursos de seu interesse!"
            
            corpo = f"""
            <html>
            <body>
            <h2>🎯 Novos Concursos Encontrados!</h2>
            <p>Encontramos {len(concursos)} novos concursos que podem interessar você:</p>
            
            """
            
            for i, concurso in enumerate(concursos, 1):
                corpo += f"""
                <div style="border: 1px solid #ddd; margin: 10px 0; padding: 15px; border-radius: 5px;">
                <h3>{i}. {concurso['titulo']}</h3>
                <p><strong>🏛️ Órgão:</strong> {concurso['orgao']}</p>
                <p><strong>💼 Cargo:</strong> {concurso['cargo']}</p>
                <p><strong>💰 Salário:</strong> {concurso['salario']}</p>
                <p><strong>👥 Vagas:</strong> {concurso['vagas']}</p>
                <p><strong>🔗 Link:</strong> <a href="{concurso['url']}">{concurso['url']}</a></p>
                </div>
                """
            
            corpo += """
            <hr>
            <p><small>Esta notificação foi enviada pelo sistema ConcursAI.<br>
            Para alterar suas preferências, acesse o painel de configurações.</small></p>
            </body>
            </html>
            """
            
            # Enviar email
            msg = MimeMultipart('alternative')
            msg['Subject'] = assunto
            msg['From'] = self.config["email"]["email_remetente"]
            msg['To'] = ', '.join(self.config["email"]["emails_destino"])
            
            part = MimeText(corpo, 'html')
            msg.attach(part)
            
            # Conectar e enviar
            server = smtplib.SMTP(self.config["email"]["smtp_server"], self.config["email"]["smtp_port"])
            server.starttls()
            server.login(self.config["email"]["email_remetente"], self.config["email"]["senha_remetente"])
            
            for destinatario in self.config["email"]["emails_destino"]:
                server.sendmail(self.config["email"]["email_remetente"], destinatario, msg.as_string())
            
            server.quit()
            print(f"✅ Email enviado para {len(self.config['email']['emails_destino'])} destinatários")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao enviar email: {e}")
            return False
    
    def criar_notificacao_desktop(self, concursos: List[Dict]):
        """Cria notificação desktop (Windows)"""
        try:
            if not concursos:
                return
            
            # Usar toast notifications no Windows
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                
                titulo = f"🎯 {len(concursos)} novos concursos!"
                mensagem = f"Encontrados concursos em: " + ", ".join([c['orgao'][:30] for c in concursos[:3]])
                
                toaster.show_toast(titulo, mensagem, duration=10, icon_path=None)
                print("✅ Notificação desktop enviada")
                
            except ImportError:
                print("ℹ️ Para notificações desktop, instale: pip install win10toast")
                
        except Exception as e:
            print(f"⚠️ Erro na notificação desktop: {e}")
    
    def executar_verificacao_completa(self):
        """Executa verificação completa e envia notificações"""
        print("🔍 Verificando novos concursos...")
        
        novos_concursos = self.verificar_novos_concursos()
        
        if novos_concursos:
            print(f"🎉 {len(novos_concursos)} novos concursos encontrados!")
            
            # Enviar notificações
            self.enviar_notificacao_email(novos_concursos)
            self.criar_notificacao_desktop(novos_concursos)
            
            # Mostrar no console
            for concurso in novos_concursos:
                print(f"📢 {concurso['titulo']} - {concurso['orgao']}")
        else:
            print("ℹ️ Nenhum concurso novo encontrado")

# Exemplo de uso
if __name__ == "__main__":
    notificador = SistemaNotificacoes()
    
    # Configurar filtros (exemplo)
    notificador.configurar_filtros(
        orgaos=["PREFEITURA", "TRIBUNAL", "BANCO"],
        cargos=["ANALISTA", "TÉCNICO", "CONTADOR"],
        estados=["SP", "RJ", "MG"],
        salario_min=5000
    )
    
    # Executar verificação
    notificador.executar_verificacao_completa()
