#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Módulo de agendamento para o sistema ConcursAI"""

import schedule
import time
import threading
from datetime import datetime
import logging
import gradio as gr
from modules.coletor_realtime import ColetorConcursosRealTime
from modules.sistema_notificacoes import SistemaNotificacoes
import os

class AgendadorConcursos:
    """Sistema de agendamento para coleta automática"""
    
    def __init__(self):
        self.ativo = False
        self.thread_agendador = None
        self.setup_logging()
        
        # Inicializar componentes
        self.coletor = ColetorConcursosRealTime()
        self.notificador = SistemaNotificacoes()
    
    def setup_logging(self):
        """Configura logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('concursai_agendador.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def tarefa_coleta_completa(self):
        """Executa coleta completa de dados"""
        try:
            self.logger.info("🚀 Iniciando coleta automática completa...")
            
            # Coletar dados
            concursos = self.coletor.coletar_todos()
            
            if concursos:
                # Salvar dados
                arquivo_atual = "concursos_chunks.csv"
                arquivo_backup = f"concursos_chunks_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                # Fazer backup se arquivo existir
                if os.path.exists(arquivo_atual):
                    os.rename(arquivo_atual, arquivo_backup)
                    self.logger.info(f"📁 Backup criado: {arquivo_backup}")
                
                # Salvar novos dados
                success = self.coletor.salvar_csv(concursos, arquivo_atual)
                
                if success:
                    self.logger.info(f"✅ Coleta concluída: {len(concursos)} concursos atualizados")
                    
                    # Verificar e enviar notificações
                    self.notificador.executar_verificacao_completa()
                else:
                    self.logger.error("❌ Erro ao salvar dados coletados")
            else:
                self.logger.warning("⚠️ Nenhum concurso coletado")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta automática: {e}")
    
    def tarefa_coleta_rapida(self):
        """Executa coleta rápida (apenas PCI)"""
        try:
            self.logger.info("⚡ Iniciando coleta rápida...")
            
            # Coletar apenas do PCI (mais rápido)
            concursos_pci = self.coletor.coletar_pci_simples()
            
            if concursos_pci:
                # Adicionar aos dados existentes
                import pandas as pd
                
                arquivo_atual = "concursos_chunks.csv"
                
                if os.path.exists(arquivo_atual):
                    df_existente = pd.read_csv(arquivo_atual)
                    df_novos = pd.DataFrame([
                        {
                            'conteudo': c.get('conteudo', c.get('titulo', '')),
                            'titulo': c.get('titulo', ''),
                            'orgao': c.get('orgao', ''),
                            'ano': c.get('ano', '2024'),
                            'cargo': c.get('cargo', 'Geral'),
                            'tipo_documento': 'edital',
                            'url': c.get('url', ''),
                            'data_publicacao': c.get('data_coleta', ''),
                            'fonte': c.get('fonte', '')
                        } for c in concursos_pci
                    ])
                    
                    # Remover duplicatas baseado no título
                    df_combinado = pd.concat([df_existente, df_novos], ignore_index=True)
                    df_combinado = df_combinado.drop_duplicates(subset=['titulo'], keep='last')
                    
                    # Salvar
                    df_combinado.to_csv(arquivo_atual, index=False)
                    self.logger.info(f"⚡ Coleta rápida concluída: {len(concursos_pci)} novos concursos")
                    
                    # Verificar notificações
                    self.notificador.executar_verificacao_completa()
                
            else:
                self.logger.info("ℹ️ Nenhum novo concurso na coleta rápida")
                
        except Exception as e:
            self.logger.error(f"❌ Erro na coleta rápida: {e}")
    
    def tarefa_verificacao_notificacoes(self):
        """Verifica e envia notificações sem coleta"""
        try:
            self.logger.info("🔔 Verificando notificações...")
            self.notificador.executar_verificacao_completa()
        except Exception as e:
            self.logger.error(f"❌ Erro na verificação de notificações: {e}")
    
    def configurar_agendamentos(self):
        """Configura os agendamentos"""
        
        # Coleta completa - 2x por dia (manhã e tarde)
        schedule.every().day.at("08:00").do(self.tarefa_coleta_completa)
        schedule.every().day.at("18:00").do(self.tarefa_coleta_completa)
        
        # Coleta rápida - a cada 2 horas durante horário comercial
        schedule.every().day.at("10:00").do(self.tarefa_coleta_rapida)
        schedule.every().day.at("12:00").do(self.tarefa_coleta_rapida)
        schedule.every().day.at("14:00").do(self.tarefa_coleta_rapida)
        schedule.every().day.at("16:00").do(self.tarefa_coleta_rapida)
        
        # Verificação de notificações - a cada hora
        schedule.every().hour.do(self.tarefa_verificacao_notificacoes)
        
        # Limpeza de logs - uma vez por semana
        schedule.every().sunday.at("02:00").do(self.limpar_logs_antigos)
        
        self.logger.info("📅 Agendamentos configurados:")
        self.logger.info("   • Coleta completa: 08:00 e 18:00")
        self.logger.info("   • Coleta rápida: 10:00, 12:00, 14:00, 16:00")
        self.logger.info("   • Notificações: a cada hora")
        self.logger.info("   • Limpeza: domingos às 02:00")
    
    def limpar_logs_antigos(self):
        """Remove logs antigos"""
        try:
            import glob
            from datetime import datetime, timedelta
            
            # Remover backups com mais de 30 dias
            data_limite = datetime.now() - timedelta(days=30)
            
            arquivos_backup = glob.glob("concursos_chunks_backup_*.csv")
            for arquivo in arquivos_backup:
                try:
                    # Extrair data do nome do arquivo
                    data_str = arquivo.split('_')[-2] + '_' + arquivo.split('_')[-1].replace('.csv', '')
                    data_arquivo = datetime.strptime(data_str, '%Y%m%d_%H%M%S')
                    
                    if data_arquivo < data_limite:
                        os.remove(arquivo)
                        self.logger.info(f"🗑️ Backup removido: {arquivo}")
                        
                except Exception:
                    continue
            
            self.logger.info("🧹 Limpeza de arquivos antigos concluída")
            
        except Exception as e:
            self.logger.error(f"❌ Erro na limpeza: {e}")
    
    def iniciar(self):
        """Inicia o agendador"""
        if self.ativo:
            self.logger.warning("⚠️ Agendador já está ativo")
            return
        
        self.configurar_agendamentos()
        self.ativo = True
        
        def executar_agendador():
            self.logger.info("🚀 Agendador iniciado")
            while self.ativo:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Verificar a cada minuto
                except Exception as e:
                    self.logger.error(f"❌ Erro no agendador: {e}")
                    time.sleep(300)  # Esperar 5 minutos em caso de erro
        
        self.thread_agendador = threading.Thread(target=executar_agendador, daemon=True)
        self.thread_agendador.start()
        
        self.logger.info("✅ Agendador iniciado com sucesso")
    
    def parar(self):
        """Para o agendador"""
        if not self.ativo:
            self.logger.warning("⚠️ Agendador não está ativo")
            return
        
        self.ativo = False
        schedule.clear()
        
        if self.thread_agendador:
            self.thread_agendador.join(timeout=5)
        
        self.logger.info("⏹️ Agendador parado")
    
    def status(self):
        """Retorna status do agendador"""
        if self.ativo:
            jobs = schedule.get_jobs()
            return {
                'ativo': True,
                'proximas_execucoes': [
                    {
                        'tarefa': str(job.job_func.__name__),
                        'proxima_execucao': str(job.next_run)
                    } for job in jobs
                ]
            }
        else:
            return {'ativo': False}
    
    def executar_agora(self, tipo_tarefa='completa'):
        """Executa tarefa imediatamente"""
        self.logger.info(f"▶️ Executando tarefa '{tipo_tarefa}' manualmente...")
        
        if tipo_tarefa == 'completa':
            self.tarefa_coleta_completa()
        elif tipo_tarefa == 'rapida':
            self.tarefa_coleta_rapida()
        elif tipo_tarefa == 'notificacoes':
            self.tarefa_verificacao_notificacoes()
        else:
            self.logger.error(f"❌ Tipo de tarefa desconhecido: {tipo_tarefa}")

# Interface para controle do agendador
def criar_interface_agendador():
    """Cria interface para controlar o agendador"""
    
    agendador = AgendadorConcursos()
    
    with gr.Blocks(title="⏰ Agendador ConcursAI") as app:
        gr.Markdown("# ⏰ Agendador Automático de Coleta")
        
        with gr.Row():
            with gr.Column():
                gr.Markdown("### 🎛️ Controles")
                
                btn_iniciar = gr.Button("▶️ Iniciar Agendador", variant="primary")
                btn_parar = gr.Button("⏹️ Parar Agendador", variant="secondary")
                
                gr.Markdown("### 🔧 Execução Manual")
                btn_coleta_completa = gr.Button("📊 Coleta Completa")
                btn_coleta_rapida = gr.Button("⚡ Coleta Rápida")
                btn_notificacoes = gr.Button("🔔 Verificar Notificações")
            
            with gr.Column():
                gr.Markdown("### 📊 Status")
                status_text = gr.Textbox(
                    label="Status do Sistema",
                    value="Sistema parado",
                    interactive=False
                )
                
                log_output = gr.Textbox(
                    label="Log de Atividades",
                    lines=10,
                    value="Aguardando ações...",
                    interactive=False
                )
        
        # Funções dos botões
        def iniciar_agendador():
            try:
                agendador.iniciar()
                status = agendador.status()
                return "✅ Agendador ativo", f"Sistema iniciado em {datetime.now()}"
            except Exception as e:
                return f"❌ Erro: {e}", f"Erro ao iniciar: {e}"
        
        def parar_agendador():
            try:
                agendador.parar()
                return "⏹️ Agendador parado", f"Sistema parado em {datetime.now()}"
            except Exception as e:
                return f"❌ Erro: {e}", f"Erro ao parar: {e}"
        
        def executar_coleta_completa():
            try:
                agendador.executar_agora('completa')
                return "Em execução...", f"Coleta completa iniciada em {datetime.now()}"
            except Exception as e:
                return f"❌ Erro: {e}", f"Erro na coleta: {e}"
        
        def executar_coleta_rapida():
            try:
                agendador.executar_agora('rapida')
                return "Em execução...", f"Coleta rápida iniciada em {datetime.now()}"
            except Exception as e:
                return f"❌ Erro: {e}", f"Erro na coleta: {e}"
        
        def verificar_notificacoes():
            try:
                agendador.executar_agora('notificacoes')
                return "Verificando...", f"Verificação de notificações em {datetime.now()}"
            except Exception as e:
                return f"❌ Erro: {e}", f"Erro nas notificações: {e}"
        
        # Conectar eventos
        btn_iniciar.click(
            fn=iniciar_agendador,
            outputs=[status_text, log_output]
        )
        
        btn_parar.click(
            fn=parar_agendador,
            outputs=[status_text, log_output]
        )
        
        btn_coleta_completa.click(
            fn=executar_coleta_completa,
            outputs=[status_text, log_output]
        )
        
        btn_coleta_rapida.click(
            fn=executar_coleta_rapida,
            outputs=[status_text, log_output]
        )
        
        btn_notificacoes.click(
            fn=verificar_notificacoes,
            outputs=[status_text, log_output]
        )
    
    return app

if __name__ == "__main__":
    # Modo standalone - executar agendador
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--interface":
        # Modo interface
        app = criar_interface_agendador()
        app.launch(server_port=7863)
    else:
        # Modo agendador
        agendador = AgendadorConcursos()
        agendador.iniciar()
        
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🛑 Parando agendador...")
            agendador.parar()
            print("✅ Agendador parado")
