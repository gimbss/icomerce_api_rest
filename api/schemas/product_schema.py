from pydantic import BaseModel, Field



class CreateProductRequest(BaseModel):
    name: str = Field(..., max_length=50)
    description: str | None = Field(None, max_length=255)
    price: float = Field(..., gt=0)
    category: str = Field(..., max_length=50)
    stock: int = Field(..., ge=0)


class UpdateProductRequest(BaseModel):
    name: str | None = Field(None, max_length=50)
    description: str | None = Field(None, max_length=255)
    price: float | None = Field(None, gt=0)
    category: str | None = Field(None, max_length=50)
    stock: int | None = Field(None, ge=0)



class ProductResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    category: str
    stock: int

    model_config = {"from_attributes": True}


class ProductCreateResponse(BaseModel):
    status: str = "success"
    product: ProductResponse


class ProductSingleResponse(BaseModel):
    status: str = "success"
    product: ProductResponse | None = None


class ProductDeleteResponse(BaseModel):
    status: str = "success"
    deleted: bool


class ProductListResponse(BaseModel):
    status: str = "success"
    products: list[ProductResponse]
    skip: int = 0
    limit: int = 20
    total: int = 0
