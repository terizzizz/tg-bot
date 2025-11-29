"""
Платежный сервис AirbaPay для Telegram бота
"""
import requests
import uuid
import logging
import asyncio
from typing import Dict, Any, Optional, Callable
from functools import wraps
from decimal import Decimal
from datetime import date, datetime

logger = logging.getLogger(__name__)


def convert_for_json_serialization(data):
    """
    Рекурсивно конвертирует Decimal, date и datetime объекты в строки
    """
    if isinstance(data, Decimal):
        return str(data)
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    elif isinstance(data, dict):
        return {key: convert_for_json_serialization(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_for_json_serialization(item) for item in data]
    else:
        return data


class AirbaPayClient:
    """Клиент для работы с AirbaPay API"""
    
    def __init__(self, base_url: str, user: str, password: str, terminal_id: str, company_id: str = "230140022645"):
        self.base_url = base_url
        self.user = user
        self.password = password
        self.terminal_id = terminal_id
        self.company_id = company_id
        self.access_token = None
        
    def _make_request(self, method: str, endpoint: str, data: Dict[str, Any] = None, 
                     headers: Dict[str, str] = None) -> Dict[str, Any]:
        """Выполняет HTTP запрос к API"""
        url = f"{self.base_url}{endpoint}"
        
        default_headers = {
            'Content-Type': 'application/json',
        }
        
        if headers:
            default_headers.update(headers)
            
        if self.access_token:
            default_headers['Authorization'] = f'Bearer {self.access_token}'
        
        if data:
            data = convert_for_json_serialization(data)
        
        try:
            response = requests.request(
                method=method,
                url=url,
                json=data,
                headers=default_headers,
                timeout=30
            )
            
            logger.info(f"Airba Pay API request: {method} {url} - Status: {response.status_code}")
            
            if response.status_code >= 400:
                logger.error(f"Airba Pay API error: {response.text}")
                
            return {
                'status_code': response.status_code,
                'data': response.json() if response.content else {},
                'success': 200 <= response.status_code < 300
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Airba Pay API request failed: {str(e)}")
            return {
                'status_code': 500,
                'data': {'error': str(e)},
                'success': False
            }
    
    def authenticate(self, payment_id: Optional[str] = None, subscription_id: Optional[str] = None) -> bool:
        """Аутентификация в AirbaPay API (синхронная)"""
        if not self.user or not self.password or not self.terminal_id:
            logger.error(f"Missing Airbapay credentials - user: {bool(self.user)}, password: {bool(self.password)}, terminal_id: {bool(self.terminal_id)}")
            return False
            
        auth_data = {
            'user': self.user,
            'password': self.password,
            'terminal_id': self.terminal_id,
        }
        
        if payment_id:
            auth_data['payment_id'] = payment_id
        
        logger.info(f"Attempting authentication with user: {self.user}, terminal_id: {self.terminal_id}")
            
        response = self._make_request('POST', '/api/v1/auth/sign-in', auth_data)
        
        if response['success'] and 'access_token' in response['data']:
            self.access_token = response['data']['access_token']
            logger.info("Authentication successful")
            return True
        
        logger.error(f"Authentication failed: {response.get('data', {})}")
        return False
    
    def add_card(self, card_data: Dict[str, Any]) -> Dict[str, Any]:
        """Добавить новую карту"""
        if not self.access_token:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('POST', '/api/v1/cards', card_data)
    
    def get_saved_cards(self, account_id: str) -> Dict[str, Any]:
        """Получить сохраненные карты"""
        if not self.access_token:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('GET', f'/api/v1/cards/{account_id}')
    
    def delete_saved_card(self, card_id: str) -> Dict[str, Any]:
        """Удалить сохраненную карту"""
        if not self.access_token:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('DELETE', f'/api/v1/cards/{card_id}')
    
    def create_payment(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Создать новый платеж"""
        if not self.access_token:
            if not self.authenticate():
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('POST', '/api/v2/payments/', payment_data)
    
    def get_payment_status(self, payment_id: str) -> Dict[str, Any]:
        """Получить статус платежа"""
        if not self.access_token:
            if not self.authenticate(payment_id=payment_id):
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('GET', f'/api/v1/payments/{payment_id}')
    
    def charge_payment(self, payment_id: str, charge_data: Dict[str, Any]) -> Dict[str, Any]:
        """Подтвердить платеж (двухэтапная оплата)"""
        if not self.access_token:
            if not self.authenticate(payment_id=payment_id):
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('PUT', '/api/v1/payments/charge', charge_data)
    
    def refund_payment(self, payment_id: str, refund_data: Dict[str, Any]) -> Dict[str, Any]:
        """Возврат платежа"""
        if not self.access_token:
            if not self.authenticate(payment_id=payment_id):
                return {'success': False, 'error': 'Authentication failed'}
        return self._make_request('DELETE', '/api/v1/payments/return', refund_data)


class PaymentService:
    """Сервис для обработки платежей через AirbaPay"""
    
    def __init__(self, client: AirbaPayClient, db, webhook_url: str = None):
        self.client = client
        self.db = db
        self.webhook_url = webhook_url or ""
    
    async def create_payment(self, user_id: int, subscription_id: int, amount: float, 
                           currency: str = "KZT", description: str = "", 
                           language: str = "ru", phone: str = "", email: str = "") -> Dict[str, Any]:
        """
        Создать платеж для абонемента
        """
        invoice_id = f"BOT_{uuid.uuid4().hex[:8].upper()}"
        
        payment_data = {
            'invoice_id': invoice_id,
            'amount': float(amount),
            'currency': currency,
            'description': description or f"Оплата абонемента #{subscription_id}",
            'auto_charge': 1,
            'card_save': False,
            'account_id': str(user_id),
            'phone': phone,
            'email': email,
            'language': language.upper(),
            'success_back_url': f"{self.webhook_url}/payment/success" if self.webhook_url else "",
            'failure_back_url': f"{self.webhook_url}/payment/failure" if self.webhook_url else "",
            'success_callback': f"{self.webhook_url}/webhook/payment/success" if self.webhook_url else "",
            'failure_callback': f"{self.webhook_url}/webhook/payment/failure" if self.webhook_url else "",
            'settlement': {
                'payments': [
                    {
                        'company_id': self.client.company_id,
                        'amount': float(amount)
                    }
                ]
            }
        }
        
        # Выполняем синхронный запрос в отдельном потоке
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = await loop.run_in_executor(None, self.client.create_payment, payment_data)
        
        if not response['success']:
            return response
            
        airba_response = response['data']
        
        # Сохраняем платеж в базу данных
        payment_id = await self.db.create_payment(
            user_id=user_id,
            subscription_id=subscription_id,
            amount=amount,
            currency=currency,
            invoice_id=invoice_id,
            airba_payment_id=airba_response.get('id', ''),
            redirect_url=airba_response.get('redirect_url', ''),
            status='pending'
        )
        
        return {
            'success': True,
            'payment_id': payment_id,
            'redirect_url': airba_response.get('redirect_url'),
            'invoice_id': invoice_id
        }
    
    async def get_payment_status(self, payment_id: int, user_id: int) -> Dict[str, Any]:
        """Получить статус платежа"""
        payment = await self.db.get_payment(payment_id, user_id)
        
        if not payment:
            return {'success': False, 'error': 'Payment not found'}
        
        if not payment.get('airba_payment_id'):
            return {'success': False, 'error': 'Airba payment ID not found'}
        
        # Выполняем синхронный запрос в отдельном потоке
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = await loop.run_in_executor(None, self.client.get_payment_status, payment['airba_payment_id'])
        
        if response['success']:
            airba_data = response['data']
            status = airba_data.get('status', 'pending')
            
            # Обновляем статус в базе данных
            await self.db.update_payment_status(
                payment_id=payment_id,
                status=status,
                transaction_id=airba_data.get('transaction_id', '')
            )
            
            return {
                'success': True,
                'status': status,
                'payment': payment,
                'airba_data': airba_data
            }
        
        return response
    
    async def refund_payment(self, payment_id: int, user_id: int, amount: float = None, reason: str = '') -> Dict[str, Any]:
        """Возврат платежа"""
        payment = await self.db.get_payment(payment_id, user_id)
        
        if not payment:
            return {'success': False, 'error': 'Payment not found or access denied'}
        
        if payment.get('status') != 'success':
            return {'success': False, 'error': 'Payment cannot be refunded in current status'}
        
        refund_amount = amount or payment.get('amount', 0)
        
        refund_data = {
            'ext_id': f"REFUND_{uuid.uuid4().hex[:8].upper()}",
            'amount': float(refund_amount),
            'reason': reason,
            'settlement': {
                'payments': [
                    {
                        'company_id': self.client.company_id,
                        'amount': float(refund_amount)
                    }
                ]
            }
        }
        
        # Выполняем синхронный запрос в отдельном потоке
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        response = await loop.run_in_executor(None, self.client.refund_payment, payment['airba_payment_id'], refund_data)
        
        if response['success']:
            await self.db.create_payment_refund(
                payment_id=payment_id,
                airba_refund_id=response['data'].get('id', ''),
                ext_id=refund_data['ext_id'],
                amount=refund_amount,
                reason=reason,
                status='success'
            )
            
        return response

