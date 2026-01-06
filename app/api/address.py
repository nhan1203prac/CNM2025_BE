from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.db.session import get_db
from app.models.address import Address
from app.models.user import User
from app.api.deps import get_current_user
from app.schemas.address import AddressCreate, AddressUpdate, AddressResponse

router = APIRouter()

@router.get("/", response_model=List[AddressResponse])
def get_addresses(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Address).filter(Address.user_id == current_user.id).all()

@router.post("/", response_model=AddressResponse)
def create_address(address_in: AddressCreate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if address_in.is_default:
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})
    
    new_address = Address(**address_in.model_dump(), user_id=current_user.id)
    db.add(new_address)
    db.commit()
    db.refresh(new_address)
    return new_address

@router.put("/{address_id}", response_model=AddressResponse)
def update_address(address_id: int, address_in: AddressUpdate, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa chỉ")

    update_data = address_in.model_dump(exclude_unset=True)
    
    if update_data.get("is_default"):
        db.query(Address).filter(Address.user_id == current_user.id).update({"is_default": False})

    for key, value in update_data.items():
        setattr(address, key, value)

    db.commit()
    db.refresh(address)
    return address

@router.delete("/{address_id}")
def delete_address(address_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    address = db.query(Address).filter(Address.id == address_id, Address.user_id == current_user.id).first()
    if not address:
        raise HTTPException(status_code=404, detail="Không tìm thấy địa chỉ")
    
    if address.is_default:
        raise HTTPException(status_code=400, detail="Không thể xóa địa chỉ mặc định")

    db.delete(address)
    db.commit()
    return {"message": "Xóa thành công"}