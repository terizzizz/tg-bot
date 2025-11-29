import io
import uuid

try:
    import qrcode
    from PIL import Image
    QR_AVAILABLE = True
except ImportError:
    QR_AVAILABLE = False


def generate_qr_code(text: str) -> io.BytesIO:
    """Генерирует QR-код и возвращает его как BytesIO объект"""
    if not QR_AVAILABLE:
        # Возвращаем пустой BytesIO если Pillow не установлен
        return io.BytesIO(b'QR code generation requires Pillow library')
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(text)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    img_bytes.seek(0)
    return img_bytes


def generate_subscription_qr(user_id: int, subscription_id: int, child_id: int = None) -> tuple[str, io.BytesIO]:
    """Генерирует уникальный QR-код для абонемента"""
    # Создаём уникальный идентификатор
    qr_id = str(uuid.uuid4())
    qr_text = f"SUBSCRIPTION:{qr_id}:{user_id}:{subscription_id}"
    if child_id:
        qr_text += f":{child_id}"
    
    qr_image = generate_qr_code(qr_text)
    return qr_id, qr_image

