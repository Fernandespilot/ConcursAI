"""
Sistema de Notificações em Tempo Real com WebSockets
Envia notificações instantâneas para os usuários sobre novos concursos e atualizações
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any, List
from fastapi import WebSocket, WebSocketDisconnect
import threading
import time

class ConnectionManager:
    """Gerenciador de conexões WebSocket"""
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_data: Dict[WebSocket, Dict] = {}
        
    async def connect(self, websocket: WebSocket, user_data: Dict = None):
        """Aceita uma nova conexão WebSocket"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_data[websocket] = user_data or {}
        
        # Enviar mensagem de boas-vindas
        await self.send_personal_message({
            "type": "welcome",
            "message": "Conectado ao ConcursAI! Você receberá notificações em tempo real.",
            "timestamp": datetime.now().isoformat(),
            "connection_id": id(websocket)
        }, websocket)
        
        logging.info(f"Nova conexão WebSocket estabelecida: {id(websocket)}")
    
    def disconnect(self, websocket: WebSocket):
        """Remove uma conexão WebSocket"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            
        if websocket in self.connection_data:
            del self.connection_data[websocket]
            
        logging.info(f"Conexão WebSocket removida: {id(websocket)}")
    
    async def send_personal_message(self, message: Dict[str, Any], websocket: WebSocket):
        """Envia mensagem para uma conexão específica"""
        try:
            await websocket.send_text(json.dumps(message, ensure_ascii=False))
        except Exception as e:
            logging.error(f"Erro ao enviar mensagem pessoal: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Envia mensagem para todas as conexões ativas"""
        if not self.active_connections:
            return
            
        disconnected = set()
        
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logging.error(f"Erro ao enviar broadcast: {e}")
                disconnected.add(connection)
        
        # Remove conexões mortas
        for connection in disconnected:
            self.disconnect(connection)
    
    async def send_to_filtered(self, message: Dict[str, Any], filter_func=None):
        """Envia mensagem para conexões filtradas"""
        if not self.active_connections:
            return
            
        disconnected = set()
        
        for connection in self.active_connections.copy():
            try:
                # Aplicar filtro se fornecido
                if filter_func and not filter_func(self.connection_data.get(connection, {})):
                    continue
                    
                await connection.send_text(json.dumps(message, ensure_ascii=False))
            except Exception as e:
                logging.error(f"Erro ao enviar mensagem filtrada: {e}")
                disconnected.add(connection)
        
        # Remove conexões mortas
        for connection in disconnected:
            self.disconnect(connection)
    
    def get_stats(self) -> Dict:
        """Retorna estatísticas das conexões"""
        return {
            "total_connections": len(self.active_connections),
            "connections_with_data": len([c for c in self.connection_data.values() if c]),
            "active_since": datetime.now().isoformat()
        }

class RealTimeNotificationSystem:
    """Sistema de notificações em tempo real"""
    
    def __init__(self):
        self.connection_manager = ConnectionManager()
        self.notification_queue: List[Dict] = []
        self.is_running = False
        self.notification_thread = None
        
    def start(self):
        """Inicia o sistema de notificações"""
        if not self.is_running:
            self.is_running = True
            self.notification_thread = threading.Thread(target=self._notification_worker)
            self.notification_thread.daemon = True
            self.notification_thread.start()
            logging.info("Sistema de notificações em tempo real iniciado")
    
    def stop(self):
        """Para o sistema de notificações"""
        self.is_running = False
        if self.notification_thread:
            self.notification_thread.join()
        logging.info("Sistema de notificações em tempo real parado")
    
    def _notification_worker(self):
        """Worker thread para processar notificações"""
        while self.is_running:
            try:
                # Processar fila de notificações
                if self.notification_queue:
                    notification = self.notification_queue.pop(0)
                    asyncio.run(self._send_notification(notification))
                
                # Aguardar antes da próxima verificação
                time.sleep(1)
                
            except Exception as e:
                logging.error(f"Erro no worker de notificações: {e}")
                time.sleep(5)
    
    async def _send_notification(self, notification: Dict):
        """Envia uma notificação"""
        try:
            await self.connection_manager.broadcast(notification)
        except Exception as e:
            logging.error(f"Erro ao enviar notificação: {e}")
    
    def queue_notification(self, notification_type: str, title: str, message: str, data: Dict = None):
        """Adiciona notificação à fila"""
        notification = {
            "type": notification_type,
            "title": title,
            "message": message,
            "data": data or {},
            "timestamp": datetime.now().isoformat(),
            "id": f"{notification_type}_{int(time.time())}"
        }
        
        self.notification_queue.append(notification)
        logging.info(f"Notificação adicionada à fila: {title}")
    
    def notify_new_concurso(self, concurso_data: Dict):
        """Notifica sobre novo concurso"""
        self.queue_notification(
            "new_concurso",
            "Novo Concurso Disponível!",
            f"Novo concurso: {concurso_data.get('titulo', 'Sem título')} - {concurso_data.get('orgao', 'Órgão não informado')}",
            concurso_data
        )
    
    def notify_system_update(self, update_info: str):
        """Notifica sobre atualização do sistema"""
        self.queue_notification(
            "system_update",
            "Atualização do Sistema",
            update_info
        )
    
    def notify_error(self, error_message: str):
        """Notifica sobre erro do sistema"""
        self.queue_notification(
            "system_error",
            "Erro do Sistema",
            error_message
        )
    
    def notify_health_status(self, health_data: Dict):
        """Notifica sobre status de saúde do sistema"""
        if health_data.get("health") in ["crítico", "atenção"]:
            self.queue_notification(
                "health_alert",
                f"Alerta de Sistema - {health_data.get('health', 'Desconhecido')}",
                f"Issues detectados: {', '.join(health_data.get('issues', []))}",
                health_data
            )
    
    async def handle_websocket(self, websocket: WebSocket, user_preferences: Dict = None):
        """Manipula conexão WebSocket"""
        await self.connection_manager.connect(websocket, user_preferences)
        
        try:
            while True:
                # Aguardar mensagens do cliente
                data = await websocket.receive_text()
                
                try:
                    message = json.loads(data)
                    await self._handle_client_message(websocket, message)
                except json.JSONDecodeError:
                    await self.connection_manager.send_personal_message({
                        "type": "error",
                        "message": "Formato de mensagem inválido"
                    }, websocket)
                    
        except WebSocketDisconnect:
            self.connection_manager.disconnect(websocket)
    
    async def _handle_client_message(self, websocket: WebSocket, message: Dict):
        """Processa mensagem do cliente"""
        message_type = message.get("type")
        
        if message_type == "ping":
            await self.connection_manager.send_personal_message({
                "type": "pong",
                "timestamp": datetime.now().isoformat()
            }, websocket)
            
        elif message_type == "subscribe":
            # Atualizar preferências de notificação
            preferences = message.get("preferences", {})
            if websocket in self.connection_manager.connection_data:
                self.connection_manager.connection_data[websocket].update(preferences)
                
            await self.connection_manager.send_personal_message({
                "type": "subscription_updated",
                "message": "Preferências de notificação atualizadas"
            }, websocket)
            
        elif message_type == "get_stats":
            stats = self.connection_manager.get_stats()
            await self.connection_manager.send_personal_message({
                "type": "stats",
                "data": stats
            }, websocket)
    
    def get_connection_stats(self) -> Dict:
        """Retorna estatísticas das conexões"""
        return self.connection_manager.get_stats()

# Instância global do sistema de notificações
notification_system = RealTimeNotificationSystem()

def start_notification_system():
    """Inicia o sistema de notificações"""
    notification_system.start()

def stop_notification_system():
    """Para o sistema de notificações"""
    notification_system.stop()

def notify_new_concurso(concurso_data: Dict):
    """Envia notificação de novo concurso"""
    notification_system.notify_new_concurso(concurso_data)

def notify_system_update(message: str):
    """Envia notificação de atualização do sistema"""
    notification_system.notify_system_update(message)

def notify_error(error_message: str):
    """Envia notificação de erro"""
    notification_system.notify_error(error_message)

def get_notification_stats():
    """Retorna estatísticas das notificações"""
    return notification_system.get_connection_stats()
