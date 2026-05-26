from pydantic import BaseModel, Field



class OrderItemInput(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    unit_price: float | None = Field(None, gt=0)


class CreateOrderRequest(BaseModel):
    items: list[OrderItemInput] = Field(..., min_length=1)


class UpdateOrderStatusRequest(BaseModel):
    status: str = Field(..., pattern=r"^(pending|confirmed|shipped|delivered|cancelled)$")



class OrderItemResponse(BaseModel):
    id: int | None = None
    product_id: int
    product_name: str
    quantity: int
    unit_price: float


class OrderResponse(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: str | None = None
    updated_at: str | None = None
    items: list[OrderItemResponse]


class OrderCreateResponse(BaseModel):
    status: str = "success"
    order: OrderResponse


class OrderSingleResponse(BaseModel):
    status: str = "success"
    order: OrderResponse | None = None


class OrderListItemResponse(BaseModel):
    id: int
    user_id: int
    status: str
    created_at: str | None = None
    items: list[OrderItemResponse]


class OrdersListResponse(BaseModel):
    status: str = "success"
    orders: list[OrderListItemResponse]
    skip: int = 0
    limit: int = 20
    total: int = 0


class OrderDeleteResponse(BaseModel):
    status: str = "success"
    deleted: bool
