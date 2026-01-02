from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from app.db.session import get_db
from app.models.order import Order
from app.models.user import User
from app.models.product import Product
from app.models.category import Category
from app.models.profile import Profile
from app.api.deps import get_current_active_admin
from app.schemas.dashboardResponse import DashboardResponse
from datetime import datetime, timedelta

router = APIRouter()

@router.get("/dashboard-data", response_model=DashboardResponse)
def get_dashboard_data(
    days: int = Query(7, ge=1, le=90), 
    db: Session = Depends(get_db),
    current_admin = Depends(get_current_active_admin)
):
    try:
        total_rev = db.query(func.sum(Order.total_amount)).filter(Order.payment_status == "PAID").scalar() or 0
        order_count = db.query(Order).count()
        product_count = db.query(Product).count()
        user_count = db.query(User).count()

        stats = [
            {"title": "Tổng doanh thu", "value": f"{float(total_rev):,.0f}đ", "icon": "payments", "trend": "+12.5%"},
            {"title": "Đơn hàng", "value": str(order_count), "icon": "shopping_cart", "trend": "+3.2%"},
            {"title": "Sản phẩm", "value": str(product_count), "icon": "inventory_2", "trend": "0%"},
            {"title": "Khách hàng", "value": str(user_count), "icon": "group", "trend": "+5.4%"},
        ]

        revenue_chart = []
        for i in range(days - 1, -1, -1):
            target_date = (datetime.now() - timedelta(days=i)).date()
            
            daily_rev = db.query(func.sum(Order.total_amount)).filter(
                func.date(Order.created_at) == target_date,
                Order.payment_status == "PAID"
            ).scalar() or 0
            
            revenue_chart.append({
                "date": target_date.strftime("%d/%m"), 
                "amount": float(daily_rev)
            })

        top_cats = db.query(
            Category.name, func.count(Product.id).label("value")
        ).join(Product).group_by(Category.name).all()

        recent_orders = db.query(Order).options(
            joinedload(Order.user).joinedload(User.profile)
        ).order_by(Order.created_at.desc()).limit(5).all()

        formatted_orders = []
        for o in recent_orders:
            name = o.user.profile.full_name if (o.user and o.user.profile and o.user.profile.full_name) else (o.user.username if o.user else "Khách")
            
            formatted_orders.append({
                "id": str(o.id),
                "customerName": name,
                "customerEmail": o.user.email if o.user else "N/A",
                "customerInitials": name[:1].upper(),
                "productName": "Sản phẩm", 
                "date": o.created_at.strftime("%d/%m/%Y"),
                "total": float(o.total_amount),
                "status": o.shipping_status 
            })

        return {
            "stats": stats,
            "revenue_chart": revenue_chart,
            "top_categories": [{"name": c.name, "value": c.value} for c in top_cats],
            "recent_orders": formatted_orders
        }

    except Exception as e:
        print(f"Admin Dashboard Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Lỗi hệ thống: {str(e)}")