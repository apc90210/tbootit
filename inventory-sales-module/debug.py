from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, AsyncMock

client = TestClient(app)

with patch('app.routers.sales.core_client.get_product', new_callable=AsyncMock) as mock_get_product, patch('app.routers.sales.core_client.create_sale', new_callable=AsyncMock) as mock_create_sale:
    mock_get_product.return_value={'id': 1, 'title': 'Test Product'}
    mock_create_sale.return_value={'id': 99}
    resp = client.post('/sales/create', data={
        'product_id': 1, 'price': 1000, 'quantity': 2, 'payment_method': 'cash',
        'warranty_days': 14, 'no_warranty': 'False', 'notes': 'Test'
    })
    print(resp.status_code)
    print(resp.content.decode('utf-8'))
