import requests
from app.core.config import settings
from datetime import datetime, timedelta
import requests

def get_ghn_shipping_details(to_district_id: int, to_ward_code: str, weight: int = 500):
    SHOP_ID = int(settings.GHN_SHOPID)
    FROM_DISTRICT_ID = 1526 
    FROM_WARD_CODE = "910347"
    
    headers = {
        "Token": settings.GHN_TOKEN,
        "ShopId": str(SHOP_ID),
        "Content-Type": "application/json"
    }

    default_res = {
        "fee": 35000,
        "expected_delivery": "3-7 ngày",
        "deadline": None
    }

    try:
        service_url = "https://dev-online-gateway.ghn.vn/shiip/public-api/v2/shipping-order/available-services"
        res_service = requests.post(service_url, json={
            "shop_id": SHOP_ID,
            "from_district": FROM_DISTRICT_ID,
            "to_district": int(to_district_id)
        }, headers=headers)
        
        services = res_service.json().get("data", [])
        service_id = services[0]["service_id"] if (services and isinstance(services, list)) else 53321

        fee_res = requests.post("https://dev-online-gateway.ghn.vn/shiip/public-api/v2/shipping-order/fee", json={
            "from_district_id": FROM_DISTRICT_ID,
            "from_ward_code": FROM_WARD_CODE,
            "service_id": service_id,
            "to_district_id": int(to_district_id),
            "to_ward_code": str(to_ward_code),
            "weight": weight, "height": 10, "length": 10, "width": 10, "insurance_value": 0
        }, headers=headers)
        
        lt_res = requests.post("https://dev-online-gateway.ghn.vn/shiip/public-api/v2/shipping-order/leadtime", json={
            "from_district_id": FROM_DISTRICT_ID, "from_ward_code": FROM_WARD_CODE,
            "to_district_id": int(to_district_id), "to_ward_code": str(to_ward_code),
            "service_id": service_id
        }, headers=headers)

        fee_data = fee_res.json()
        lt_data = lt_res.json()

        fee = fee_data["data"]["total"] if fee_data.get("code") == 200 else 35000
        
        expected_delivery = "3-7 ngày"
        deadline = None
        
        if lt_data.get("code") == 200:
            ts = lt_data["data"]["leadtime"]
            dt = datetime.fromtimestamp(ts)
            expected_delivery = dt.strftime("%d/%m/%Y")
            deadline = (dt + timedelta(days=1)).strftime("%d/%m/%Y")

        return {
            "fee": fee,
            "expected_delivery": expected_delivery,
            "deadline": deadline
        }

    except Exception as e:
        print(f"GHN Global Error: {e}")
        return default_res
    

    
def create_ghn_shipping_order(order, address):
    url = "https://dev-online-gateway.ghn.vn/shiip/public-api/v2/shipping-order/create"
    SHOP_ID = int(settings.GHN_SHOPID)
    FROM_DISTRICT_ID = 1526
    
    headers = {
        "Token": settings.GHN_TOKEN,
        "ShopId": str(SHOP_ID),
        "Content-Type": "application/json"
    }

    try:
        service_url = "https://dev-online-gateway.ghn.vn/shiip/public-api/v2/shipping-order/available-services"
        res_service = requests.post(service_url, json={
            "shop_id": SHOP_ID,
            "from_district": FROM_DISTRICT_ID,
            "to_district": int(address.district_id)
        }, headers=headers)
        
        services = res_service.json().get("data", [])
        service_id = services[0]["service_id"] if (services and isinstance(services, list)) else 53321

        test_district_id = 1442 
        test_ward_code = "20101"

        ghn_items = []
        for item in order.items:
            ghn_items.append({
                "name": item.product.name,
                "code": f"PROD-{item.product_id}",
                "quantity": item.quantity,
                "price": int(item.product.price), 
                "weight": 200
            })

        total_weight = sum(it["quantity"] * 200 for it in ghn_items)
        payload = {
            "payment_type_id": 2, # Khách trả tiền phí ship
            "note": "Cho xem hàng, không cho thử",
            "required_note": "CHOXEMHANGKHONGTHU",
            "to_name": address.receiver_name,
            "to_phone": address.receiver_phone,
            "to_address": str(address.street_details),
            "to_ward_code": str(address.ward_code),
            "to_district_id": int(address.district_id),
            "cod_amount": int(order.subtotal) if order.payment_status == "PENDING" else 0,
            "content": f"Đơn hàng #{order.id} ({len(ghn_items)} món)",
            "items": ghn_items,
            "weight": total_weight,
            "length": 10,
            "width": 10,
            "height": 10,
            "service_id": service_id 
        }
        print(f"GHN addreess: {address.district_id, address.street_details, address.ward_code}")

        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if data.get("code") == 200:
            return data["data"]["order_code"]
        else:
            print(f"GHN Error Message: {data.get('message')}")
            return None
            
    except Exception as e:
        print(f"GHN Creation Error: {e}")
        return None